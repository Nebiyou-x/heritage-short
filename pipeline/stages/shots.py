import os
from pathlib import Path
from typing import Any

from pipeline.common import OUTPUTS_DIR, compute_hash, is_mock_mode, run_logged_generation
from pipeline.media import require_ffmpeg_filters, run_ffmpeg, verify_video


FPS = 24
FORMATS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
}


def _render_still_motion(
    image_path: Path,
    output_path: Path,
    duration: float,
    width: int,
    height: int,
) -> None:
    frames = round(duration * FPS)
    zoompan = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='min(1+0.08*on/{frames},1.08)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d=1:s={width}x{height}:fps={FPS},format=yuv420p"
    )
    temporary_path = output_path.with_name(f".{output_path.stem}.tmp.mp4")
    try:
        run_ffmpeg([
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(image_path),
            "-vf",
            zoompan,
            "-t",
            f"{duration:.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            os.getenv("FFMPEG_PRESET", "medium"),
            "-crf",
            os.getenv("FFMPEG_CRF", "20"),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(temporary_path),
        ])
        verify_video(temporary_path, duration, width, height, require_audio=False)
        temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def run_shots_stage(
    storyboard: dict[str, Any],
    keyframe_map: dict[str, str],
) -> dict[str, str]:
    stage_dir = OUTPUTS_DIR / "shots"
    stage_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}

    if not is_mock_mode():
        require_ffmpeg_filters({"scale", "crop", "zoompan"})

    for shot in storyboard["shots"]:
        shot_id = shot["shot_id"]
        image_path = Path(keyframe_map[shot_id])
        if not image_path.is_file():
            raise FileNotFoundError(f"Keyframe for {shot_id} does not exist: {image_path}")

        for aspect_ratio in storyboard["aspect_ratios"]:
            width, height = FORMATS[aspect_ratio]
            payload = {
                "stage": "shots",
                "shot_id": shot_id,
                "keyframe": image_path.name,
                "duration_sec": shot["duration_sec"],
                "aspect_ratio": aspect_ratio,
                "width": width,
                "height": height,
                "fps": FPS,
                "zoom": 0.08,
            }
            cache_key = compute_hash(payload)
            extension = ".mock.json" if is_mock_mode() else ".mp4"
            output_path = stage_dir / f"{shot_id}_{aspect_ratio.replace(':', 'x')}_{cache_key}{extension}"
            result_key = f"{shot_id}:{aspect_ratio}"

            if output_path.exists():
                results[result_key] = str(output_path)
                continue

            if is_mock_mode():
                output_path.write_text(
                    f"keyframe={image_path}\nduration={shot['duration_sec']}\n"
                    f"aspect_ratio={aspect_ratio}\n",
                    encoding="utf-8",
                )
                results[result_key] = str(output_path)
                continue

            run_logged_generation(
                lambda: _render_still_motion(
                    image_path,
                    output_path,
                    float(shot["duration_sec"]),
                    width,
                    height,
                ),
                {
                    "stage": "shots",
                    "provider": "ffmpeg",
                    "shot_id": shot_id,
                    "aspect_ratio": aspect_ratio,
                    "cache_key": cache_key,
                    "model": "ffmpeg-ken-burns",
                    "parameters": payload,
                    "seed": shot["seed"],
                    "cost_usd": 0.0,
                    "output_path": str(output_path),
                },
                retries=1,
            )
            results[result_key] = str(output_path)

    return results
