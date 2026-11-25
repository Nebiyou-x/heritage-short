import time
from pathlib import Path
from typing import Dict, Any
from pipeline.common import OUTPUTS_DIR, compute_hash, is_mock_mode, log_run, run_with_retry


def run_narration_stage(storyboard: Dict[str, Any]) -> Dict[str, str]:
    stage_dir = OUTPUTS_DIR / "narration"
    stage_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, str] = {}

    for shot in storyboard["shots"]:
        payload = {
            "stage": "narration",
            "shot_id": shot["shot_id"],
            "language": storyboard["language"],
            "narration_am": shot["narration_am"],
            "subtitle_en": shot["subtitle_en"],
        }
        cache_key = compute_hash(payload)
        out_path = stage_dir / f"{shot['shot_id']}_{cache_key}.txt"

        if out_path.exists():
            results[shot["shot_id"]] = str(out_path)
            continue

        start = time.perf_counter()

        def _generate() -> None:
            if is_mock_mode():
                time.sleep(0.05)
                out_path.write_text(
                    f"AM: {shot['narration_am']}\nEN: {shot['subtitle_en']}\n",
                    encoding="utf-8",
                )
            else:
                raise NotImplementedError("Connect Gemini 3.8 Flash TTS when USE_MOCK=0")

        run_with_retry(_generate, retries=3)
        latency_sec = round(time.perf_counter() - start, 3)

        log_run({
            "stage": "narration",
            "shot_id": shot["shot_id"],
            "cache_key": cache_key,
            "model": "mock-gemini-3.8-flash-tts" if is_mock_mode() else "gemini-3.8-flash-tts",
            "language": storyboard["language"],
            "latency_sec": latency_sec,
            "cost_usd": 0.0,
            "output_path": str(out_path),
        })
        results[shot["shot_id"]] = str(out_path)

    return results