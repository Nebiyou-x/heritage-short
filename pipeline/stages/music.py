import time
from pathlib import Path
from typing import Dict, Any
from pipeline.common import OUTPUTS_DIR, compute_hash, is_mock_mode, log_run, run_with_retry


def run_music_stage(storyboard: Dict[str, Any]) -> Dict[str, str]:
    stage_dir = OUTPUTS_DIR / "music"
    stage_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, str] = {}

    for cue in storyboard["music_cues"]:
        payload = {
            "stage": "music",
            "cue_id": cue["id"],
            "caption": cue["caption"],
            "tempo_bpm": cue["tempo_bpm"],
            "duration_sec": cue["end_sec"] - cue["start_sec"],
            "seed": cue["seed"],
        }
        cache_key = compute_hash(payload)
        out_path = stage_dir / f"{cue['id']}_{cache_key}.wav.meta.txt"

        if out_path.exists():
            results[cue["id"]] = str(out_path)
            continue

        start = time.perf_counter()

        def _generate() -> None:
            if is_mock_mode():
                time.sleep(0.05)
                out_path.write_text(str(payload), encoding="utf-8")
            else:
                raise NotImplementedError("Connect ACE-Step 1.5 generator when USE_MOCK=0")

        run_with_retry(_generate, retries=3)
        latency_sec = round(time.perf_counter() - start, 3)

        log_run({
            "stage": "music",
            "cue_id": cue["id"],
            "cache_key": cache_key,
            "model": "mock-ace-step-1.5" if is_mock_mode() else "ace-step-1.5",
            "seed": cue["seed"],
            "latency_sec": latency_sec,
            "cost_usd": 0.0,
            "output_path": str(out_path),
        })
        results[cue["id"]] = str(out_path)

    return results