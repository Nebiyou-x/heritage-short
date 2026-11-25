import os
import time
from pathlib import Path
from typing import Dict, Any
from pipeline.common import (
    OUTPUTS_DIR,
    compute_hash,
    is_mock_mode,
    run_logged_generation,
)
from pipeline.providers import (
    CLOUDFLARE_IMAGE_MODEL,
    generate_cloudflare_image,
    is_retryable_provider_error,
)


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
    provider = os.getenv(
        "KEYFRAMES_PROVIDER",
        "mock" if is_mock_mode() else "cloudflare",
    ).strip().lower()
    if provider not in {"mock", "cloudflare"}:
        raise ValueError("KEYFRAMES_PROVIDER must be 'mock' or 'cloudflare'")
    model = "mock-placeholder" if provider == "mock" else CLOUDFLARE_IMAGE_MODEL
    extension = "png" if provider == "mock" else "jpg"

    for shot in storyboard["shots"]:
        prompt = (
            f"{storyboard['style_block']}. "
            f"Character: {storyboard['character_ref']['description']}. "
            f"Shot: {shot['image_prompt']}"
        )
        payload = {
            "stage": "keyframes",
            "provider": provider,
            "model": model,
            "shot_id": shot["shot_id"],
            "prompt": prompt,
            "seed": shot["seed"],
            "steps": 4 if provider == "cloudflare" else None,
        }
        cache_key = compute_hash(payload)
        out_path = stage_dir / f"{shot['shot_id']}_{cache_key}.{extension}"

        if out_path.exists():
            results[shot["shot_id"]] = str(out_path)
            continue

        entry = {
            "stage": "keyframes",
            "provider": provider,
            "shot_id": shot["shot_id"],
            "cache_key": cache_key,
            "model": model,
            "parameters": {
                "prompt": prompt,
                "seed": shot["seed"],
                "steps": 4 if provider == "cloudflare" else None,
            },
            "seed": shot["seed"],
            "cost_usd": 0.0 if provider == "mock" else None,
            "output_path": str(out_path),
        }

        if provider == "mock":
            def _generate_mock() -> None:
                time.sleep(0.05)
                _write_placeholder_png(out_path, prompt)

            run_logged_generation(_generate_mock, entry)
        else:
            image = run_logged_generation(
                lambda: generate_cloudflare_image(prompt, shot["seed"]),
                entry,
                should_retry=is_retryable_provider_error,
            )
            out_path.write_bytes(image)
        results[shot["shot_id"]] = str(out_path)

    return results