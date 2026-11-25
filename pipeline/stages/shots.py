import time
from pathlib import Path
from typing import Dict, Any
from pipeline.common import OUTPUTS_DIR, compute_hash, is_mock_mode, log_run, run_with_retry


def run_shots_stage(storyboard: Dict[str, Any], keyframe_map: Dict[str, str]) -> Dict[str, str]:
    stage_dir = OUTPUTS_DIR / "shots"
    stage_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, str] = {}

    for shot in storyboard["shots"]:
        kf_path = keyframe_map[shot["shot_id"]]
        payload = {
            "stage": "shots",
            "shot_id": shot["shot_id"],
            "keyframe": Path(kf_path).name,
            "motion_prompt": shot["motion_prompt"],
            "duration_sec": shot["duration_sec"],
            "seed": shot["seed"],
        }
        cache_key = compute_hash(payload)
        out_path = stage_dir / f"{shot['shot_id']}_{cache_key}.mp4.meta.json"

        if out_path.exists():
            results[shot["shot_id"]] = str(out_path)
            continue

        start = time.perf_counter()

        def _generate() -> None:
            if is_mock_mode():
                time.sleep(0.05)
                out_path.write_text(
                    f"keyframe={kf_path}\nmotion={shot['motion_prompt']}\nduration={shot['duration_sec']}\n",
                    encoding="utf-8",
                )
            else:
                raise NotImplementedError("Connect Kaggle Wan 2.2 TI2V-5B runner when USE_MOCK=0")

        run_with_retry(_generate, retries=3)
        latency_sec = round(time.perf_counter() - start, 3)

        log_run({
            "stage": "shots",
            "shot_id": shot["shot_id"],
            "cache_key": cache_key,
            "model": "mock-wan-2.2-ti2v-5b" if is_mock_mode() else "wan-2.2-ti2v-5b",
            "seed": shot["seed"],
            "latency_sec": latency_sec,
            "gpu_minutes": 0.0 if is_mock_mode() else None,
            "cost_usd": 0.0,
            "output_path": str(out_path),
        })
        results[shot["shot_id"]] = str(out_path)

    return results