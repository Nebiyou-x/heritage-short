import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pipeline.common import (
    END_CARD_DURATION_SEC,
    OUTPUTS_DIR,
    compute_hash,
    is_mock_mode,
    log_run,
    run_logged_generation,
)
from pipeline.media import probe_media, require_ffmpeg_filters, run_ffmpeg, verify_video
from pipeline.stages.shots import FORMATS, FPS


def _format_srt_time(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    total_sec, ms = divmod(total_ms, 1000)
    hrs, remainder = divmod(total_sec, 3600)
    mins, secs = divmod(remainder, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def _escaped_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _write_concat_file(path: Path, inputs: list[Path]) -> None:
    lines = []
    for input_path in inputs:
        if not input_path.is_file():
            raise FileNotFoundError(f"Media input does not exist: {input_path}")
        escaped = str(input_path.resolve()).replace("\\", "\\\\").replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_narration_duration(path: Path, shot_id: str, shot_duration: float) -> None:
    metadata = probe_media(path)
    try:
        audio_duration = float(metadata["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Narration audio has no valid duration: {path}") from exc
    if audio_duration > shot_duration + 0.25:
        raise ValueError(
            f"Narration for {shot_id} is {audio_duration:.2f}s, "
            f"longer than its {shot_duration:.2f}s shot; extend the shot or shorten the line"
        )


def _render_end_card(output: Path, srt_path: Path, width: int, height: int) -> None:
    style = "FontSize=48,PrimaryColour=&H00FFFFFF,Outline=2,Shadow=0,Alignment=5"
    subtitle_filter = (
        f"subtitles=filename='{_escaped_filter_path(srt_path)}':"
        f"force_style='{style}'"
    )
    run_ffmpeg([
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s={width}x{height}:r={FPS}:d={END_CARD_DURATION_SEC}",
        "-vf",
        subtitle_filter,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        os.getenv("FFMPEG_PRESET", "medium"),
        "-crf",
        os.getenv("FFMPEG_CRF", "20"),
        "-pix_fmt",
        "yuv420p",
        "-t",
        str(END_CARD_DURATION_SEC),
        str(output),
    ])


def _render_export(
    storyboard: dict[str, Any],
    aspect_ratio: str,
    shots: dict[str, str],
    music_path: Path,
    narration: dict[str, str],
    subtitles_path: Path,
    output_path: Path,
    temp_dir: Path,
) -> None:
    width, height = FORMATS[aspect_ratio]
    duration = sum(float(shot["duration_sec"]) for shot in storyboard["shots"])
    total_duration = duration + END_CARD_DURATION_SEC
    shot_clips = [
        Path(shots[f"{shot['shot_id']}:{aspect_ratio}"])
        for shot in storyboard["shots"]
    ]
    for clip in shot_clips:
        if not clip.is_file():
            raise FileNotFoundError(f"Rendered shot clip does not exist: {clip}")

    shot_concat = temp_dir / f"shots_{aspect_ratio.replace(':', 'x')}.ffconcat"
    shot_video = temp_dir / f"shots_{aspect_ratio.replace(':', 'x')}.mp4"
    _write_concat_file(shot_concat, shot_clips)
    run_ffmpeg([
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(shot_concat),
        "-c",
        "copy",
        str(shot_video),
    ])

    subtitled_video = temp_dir / f"subtitled_{aspect_ratio.replace(':', 'x')}.mp4"
    subtitle_filter = (
        f"subtitles=filename='{_escaped_filter_path(subtitles_path)}':"
        "force_style='FontSize=30,Outline=2,Shadow=1,Alignment=2'"
    )
    run_ffmpeg([
        "-i",
        str(shot_video),
        "-vf",
        subtitle_filter,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        os.getenv("FFMPEG_PRESET", "medium"),
        "-crf",
        os.getenv("FFMPEG_CRF", "20"),
        "-pix_fmt",
        "yuv420p",
        str(subtitled_video),
    ])

    end_card_srt = temp_dir / f"end_card_{aspect_ratio.replace(':', 'x')}.srt"
    end_card_srt.write_text(
        "1\n00:00:00,500 --> 00:00:03,500\nMade with AI\\NHeritage Short\n",
        encoding="utf-8",
    )
    end_card = temp_dir / f"end_card_{aspect_ratio.replace(':', 'x')}.mp4"
    _render_end_card(end_card, end_card_srt, width, height)

    silent_concat = temp_dir / f"silent_{aspect_ratio.replace(':', 'x')}.ffconcat"
    silent_video = temp_dir / f"silent_{aspect_ratio.replace(':', 'x')}.mp4"
    _write_concat_file(silent_concat, [subtitled_video, end_card])
    run_ffmpeg([
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(silent_concat),
        "-c",
        "copy",
        str(silent_video),
    ])

    filter_parts = []
    voice_labels = []
    cursor = 0.0
    voice_input_start = 2
    for index, shot in enumerate(storyboard["shots"]):
        audio_path = Path(narration[shot["shot_id"]])
        if not audio_path.is_file():
            raise FileNotFoundError(f"Narration audio does not exist: {audio_path}")
        shot_duration = float(shot["duration_sec"])
        _validate_narration_duration(audio_path, shot["shot_id"], shot_duration)
        input_index = voice_input_start + index
        delay_ms = round(cursor * 1000)
        label = f"voice{index}"
        filter_parts.append(
            f"[{input_index}:a]aresample=48000,"
            "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"apad,atrim=duration={shot_duration:.3f},"
            f"adelay={delay_ms}|{delay_ms}[{label}]"
        )
        voice_labels.append(f"[{label}]")
        cursor += float(shot["duration_sec"])

    filter_parts.append(
        f"{''.join(voice_labels)}amix=inputs={len(voice_labels)}:"
        "duration=longest:dropout_transition=0,"
        f"apad=pad_dur={END_CARD_DURATION_SEC},atrim=duration={total_duration:.3f}[voice]"
    )
    filter_parts.append(
        f"[1:a]aresample=48000,"
        "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
        f"atrim=duration={duration:.3f},volume=0.35,"
        f"afade=t=out:st={max(duration - 2, 0):.3f}:d=2,"
        f"apad=pad_dur={END_CARD_DURATION_SEC}[music]"
    )
    filter_parts.append(
        "[voice]asplit=2[voice_sc][voice_mix]"
    )
    filter_parts.append(
        "[music][voice_sc]sidechaincompress="
        "threshold=0.02:ratio=6:attack=300:release=1500[ducked]"
    )
    filter_parts.append(
        f"[ducked][voice_mix]amix=inputs=2:duration=longest:dropout_transition=0,"
        "loudnorm=I=-14:TP=-1:LRA=11[aout]"
    )

    temporary_output = output_path.with_name(f".{output_path.stem}.tmp.mp4")
    command = ["-i", str(silent_video), "-stream_loop", "-1", "-i", str(music_path)]
    command.extend(["-i", str(narration[storyboard["shots"][0]["shot_id"]])])
    for shot in storyboard["shots"][1:]:
        command.extend(["-i", str(narration[shot["shot_id"]])])
    command.extend([
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        "0:v:0",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        str(temporary_output),
    ])
    try:
        run_ffmpeg(command)
        verify_video(temporary_output, total_duration, width, height)
        temporary_output.replace(output_path)
    finally:
        temporary_output.unlink(missing_ok=True)


def run_assemble_stage(
    storyboard: dict[str, Any],
    keyframes: dict[str, str],
    shots: dict[str, str],
    music: dict[str, str],
    narration: dict[str, str],
) -> dict[str, str]:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    if len(music) != 1:
        raise ValueError("The production assembler currently requires exactly one music track")

    duration = sum(float(shot["duration_sec"]) for shot in storyboard["shots"])
    payload = {
        "stage": "assemble",
        "project_title": storyboard["project_title"],
        "aspect_ratios": storyboard["aspect_ratios"],
        "duration_sec": duration,
        "end_card_sec": END_CARD_DURATION_SEC,
        "subtitles": [shot["subtitle_en"] for shot in storyboard["shots"]],
        "keyframes": keyframes,
        "shots": shots,
        "music": music,
        "narration": narration,
    }
    cache_key = compute_hash(payload)
    exports = {
        aspect_ratio: str(
            OUTPUTS_DIR
            / f"film_{aspect_ratio.replace(':', 'x')}_{cache_key}.mp4"
        )
        for aspect_ratio in storyboard["aspect_ratios"]
    }
    manifest_path = OUTPUTS_DIR / f"edit_manifest_{cache_key}.json"
    subtitles_path = OUTPUTS_DIR / f"subtitles_{cache_key}.srt"

    if not is_mock_mode():
        require_ffmpeg_filters({"subtitles", "sidechaincompress", "loudnorm"})
        for aspect_ratio in storyboard["aspect_ratios"]:
            width, height = FORMATS[aspect_ratio]
            output_path = Path(exports[aspect_ratio])
            if output_path.exists():
                verify_video(output_path, duration + END_CARD_DURATION_SEC, width, height)

    if (
        manifest_path.is_file()
        and subtitles_path.is_file()
        and all(Path(path).is_file() for path in exports.values())
    ):
        return exports

    srt_lines = []
    cursor = 0.0
    for index, shot in enumerate(storyboard["shots"], start=1):
        end = cursor + float(shot["duration_sec"])
        srt_lines.append(
            f"{index}\n{_format_srt_time(cursor)} --> {_format_srt_time(end)}\n"
            f"{shot['subtitle_en']}\n"
        )
        cursor = end
    subtitles_path.write_text("\n".join(srt_lines), encoding="utf-8")

    manifest = {
        "project_title": storyboard["project_title"],
        "story_duration_sec": duration,
        "end_card_duration_sec": END_CARD_DURATION_SEC,
        "total_duration_sec": duration + END_CARD_DURATION_SEC,
        "exports": exports,
        "subtitles": str(subtitles_path),
        "end_card": "Made with AI — Heritage Short Pipeline",
        "music_license": os.getenv("MUSIC_LICENSE") if not is_mock_mode() else None,
        "music_attribution": os.getenv("MUSIC_ATTRIBUTION") if not is_mock_mode() else None,
        "ducking_settings": {
            "threshold": 0.02,
            "ratio": 6,
            "attack_ms": 300,
            "release_ms": 1500,
        },
        "loudness_target_lufs": -14.0,
        "true_peak_db": -1.0,
    }

    if is_mock_mode():
        manifest_path.write_text(
            json.dumps({**manifest, "mock_mode": True}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log_run({
            "stage": "assemble",
            "cache_key": cache_key,
            "tool": "mock-manifest-only",
            "latency_sec": 0.0,
            "cost_usd": 0.0,
            "success": True,
            "manifest_path": str(manifest_path),
        })
        return exports

    with tempfile.TemporaryDirectory(prefix="heritage-assemble-", dir=OUTPUTS_DIR) as temp:
        temp_dir = Path(temp)
        for aspect_ratio, output in exports.items():
            output_path = Path(output)
            run_logged_generation(
                lambda ar=aspect_ratio, out=output_path: _render_export(
                    storyboard,
                    ar,
                    shots,
                    Path(next(iter(music.values()))),
                    narration,
                    subtitles_path,
                    out,
                    temp_dir,
                ),
                {
                    "stage": "assemble",
                    "provider": "ffmpeg",
                    "aspect_ratio": aspect_ratio,
                    "cache_key": cache_key,
                    "model": "ffmpeg-assembly",
                    "parameters": {
                        "story_duration_sec": duration,
                        "end_card_sec": END_CARD_DURATION_SEC,
                        "loudness_target_lufs": -14.0,
                        "true_peak_db": -1.0,
                    },
                    "seed": None,
                    "cost_usd": 0.0,
                    "output_path": str(output_path),
                },
                retries=1,
            )

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    log_run({
        "stage": "assemble",
        "cache_key": cache_key,
        "tool": "ffmpeg",
        "latency_sec": None,
        "cost_usd": 0.0,
        "success": True,
        "manifest_path": str(manifest_path),
    })
    return exports
