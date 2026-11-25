import json
import time
from pathlib import Path
from typing import Dict, Any
from pipeline.common import OUTPUTS_DIR, compute_hash, is_mock_mode, log_run


def _format_srt_time(seconds: float) -> str:
    ms = int(round((seconds - int(seconds)) * 1000))
    total_sec = int(seconds)
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def run_assemble_stage(
    storyboard: Dict[str, Any],
    keyframes: Dict[str, str],
    shots: Dict[str, str],
    music: Dict[str, str],
    narration: Dict[str, str],
) -> Dict[str, str]:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage": "assemble",
        "aspect_ratios": storyboard["aspect_ratios"],
        "keyframes": keyframes,
        "shots": shots,
        "music": music,
        "narration": narration,
    }
    cache_key = compute_hash(payload)

    # Write SRT subtitles for final assembly
    srt_lines = []
    cursor = 0.0
    for idx, shot in enumerate(storyboard["shots"], start=1):
        start_t = _format_srt_time(cursor)
        end_t = _format_srt_time(cursor + float(shot["duration_sec"]))
        srt_lines.append(f"{idx}\n{start_t} --> {end_t}\n{shot['subtitle_en']}\n")
        cursor += float(shot["duration_sec"])

    srt_path = OUTPUTS_DIR / f"subtitles_{cache_key}.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    manifest_path = OUTPUTS_DIR / f"edit_manifest_{cache_key}.json"
    manifest = {
        "project_title": storyboard["project_title"],
        "total_duration_sec": cursor,
        "exports": {
            ar: str(OUTPUTS_DIR / f"film_{ar.replace(':', 'x')}_{cache_key}.mp4")
            for ar in storyboard["aspect_ratios"]
        },
        "subtitles": str(srt_path),
        "end_card": "Made with AI — Heritage Short Pipeline",
        "ducking_settings": {"threshold": 0.02, "ratio": 6, "attack_ms": 300, "release_ms": 1500},
        "loudness_target_lufs": -14.0,
        "true_peak_db": -1.0,
    }

    if not manifest_path.exists():
        start = time.perf_counter()
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        if is_mock_mode():
            for exp_file in manifest["exports"].values():
                Path(exp_file).write_text("MOCK_MP4_PLACEHOLDER\n", encoding="utf-8")
        latency_sec = round(time.perf_counter() - start, 3)
        log_run({
            "stage": "assemble",
            "cache_key": cache_key,
            "tool": "ffmpeg-manifest-mock" if is_mock_mode() else "ffmpeg",
            "latency_sec": latency_sec,
            "cost_usd": 0.0,
            "manifest_path": str(manifest_path),
        })

    return manifest["exports"]