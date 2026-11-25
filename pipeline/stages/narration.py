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
    GEMINI_TTS_MODEL,
    generate_gemini_speech,
    is_retryable_provider_error,
)


def run_narration_stage(storyboard: Dict[str, Any]) -> Dict[str, str]:
    stage_dir = OUTPUTS_DIR / "narration"
    stage_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, str] = {}
    provider = os.getenv(
        "NARRATION_PROVIDER",
        "mock" if is_mock_mode() else "gemini",
    ).strip().lower()
    if provider not in {"mock", "gemini"}:
        raise ValueError("NARRATION_PROVIDER must be 'mock' or 'gemini'")
    model = "mock-placeholder" if provider == "mock" else GEMINI_TTS_MODEL
    voice = os.getenv("GEMINI_TTS_VOICE", "Kore")
    style = os.getenv(
        "GEMINI_TTS_STYLE",
        "Warm, conversational narration with a natural storytelling cadence.",
    )

    for shot in storyboard["shots"]:
        payload = {
            "stage": "narration",
            "provider": provider,
            "model": model,
            "shot_id": shot["shot_id"],
            "language": storyboard["language"],
            "narration_am": shot["narration_am"],
            "voice": voice if provider == "gemini" else None,
            "style": style if provider == "gemini" else None,
        }
        cache_key = compute_hash(payload)
        extension = "txt" if provider == "mock" else "wav"
        out_path = stage_dir / f"{shot['shot_id']}_{cache_key}.{extension}"

        if out_path.exists():
            results[shot["shot_id"]] = str(out_path)
            continue

        entry = {
            "stage": "narration",
            "provider": provider,
            "shot_id": shot["shot_id"],
            "cache_key": cache_key,
            "model": model,
            "language": storyboard["language"],
            "parameters": {
                "text": shot["narration_am"],
                "voice": voice if provider == "gemini" else None,
                "style": style if provider == "gemini" else None,
                "output_format": "wav" if provider == "gemini" else "text",
            },
            "seed": None,
            "cost_usd": 0.0 if provider == "mock" else None,
            "output_path": str(out_path),
        }

        if provider == "mock":
            def _generate_mock() -> None:
                time.sleep(0.05)
                out_path.write_text(
                    f"AM: {shot['narration_am']}\nEN: {shot['subtitle_en']}\n",
                    encoding="utf-8",
                )

            run_logged_generation(_generate_mock, entry)
        else:
            audio = run_logged_generation(
                lambda: generate_gemini_speech(
                    shot["narration_am"],
                    voice,
                    style,
                ),
                entry,
                should_retry=is_retryable_provider_error,
            )
            out_path.write_bytes(audio)
        results[shot["shot_id"]] = str(out_path)

    return results