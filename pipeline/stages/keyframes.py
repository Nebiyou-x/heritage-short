import time
from pathlib import Path
from typing import Dict, Any
from pipeline.common import OUTPUTS_DIR, compute_hash, is_mock_mode, log_run, run_with_retry


def _write_placeholder_png(path: Path, label: str) -> None:
    # Minimal valid 1x1 PNG bytes so downstream FFmpeg assembly works even in mock mode
    png_1x1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
        b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    path.write_bytes(png_1x1)
    path.with_suffix(".txt").write_text(label, encoding="utf-8")


def run_keyframes_stage(storyboard: Dict[str, Any]) -> Dict[str, str]:
    stage_dir = OUTPUTS_DIR / "keyframes"
    stage_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, str] = {}

    for shot in storyboard["shots"]:
        payload = {
            "stage": "keyframes",
            "shot_id": shot["shot_id"],
            "style_block": storyboard["style_block"],
            "character_ref": storyboard["character_ref"],
            "image_prompt": shot["image_prompt"],
            "seed": shot["seed"],
        }
        cache_key = compute_hash(payload)
        out_path = stage_dir / f"{shot['shot_id']}_{cache_key}.png"

        if out_path.exists():
            results[shot["shot_id"]] = str(out_path)
            continue

        start = time.perf_counter()

        def _generate() -> None:
            if is_mock_mode():
                time.sleep(0.05)
                _write_placeholder_png(out_path, f"{payload['style_block']} | {payload['image_prompt']}")
            else:
                # Replace with Cloudflare Workers AI FLUX.2 klein / FLUX.1 schnell call
                raise NotImplementedError("Connect Cloudflare Workers AI endpoint when USE_MOCK=0")

        run_with_retry(_generate, retries=3)
        latency_sec = round(time.perf_counter() - start, 3)

        log_run({
            "stage": "keyframes",
            "shot_id": shot["shot_id"],
            "cache_key": cache_key,
            "model": "mock-flux2-klein" if is_mock_mode() else "flux-2-klein-4b",
            "seed": shot["seed"],
            "latency_sec": latency_sec,
            "cost_usd": 0.0,
            "output_path": str(out_path),
        })
        results[shot["shot_id"]] = str(out_path)

    return results