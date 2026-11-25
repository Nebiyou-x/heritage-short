import hashlib
import os
import shutil
from pathlib import Path
from typing import Any

from pipeline.common import OUTPUTS_DIR, compute_hash, is_mock_mode, log_run
from pipeline.media import probe_media


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_music_stage(storyboard: dict[str, Any]) -> dict[str, str]:
    stage_dir = OUTPUTS_DIR / "music"
    stage_dir.mkdir(parents=True, exist_ok=True)

    if is_mock_mode():
        results = {}
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
            output_path = stage_dir / f"{cue['id']}_{cache_key}.mock.json"
            output_path.write_text(str(payload), encoding="utf-8")
            log_run({
                **payload,
                "cache_key": cache_key,
                "model": "mock-placeholder",
                "latency_sec": 0.0,
                "cost_usd": 0.0,
                "success": True,
                "output_path": str(output_path),
            })
            results[cue["id"]] = str(output_path)
        return results

    if len(storyboard["music_cues"]) != 1:
        raise ValueError("The current production assembler supports exactly one continuous music cue")

    configured_path = os.getenv("MUSIC_FILE", "").strip()
    if not configured_path:
        raise RuntimeError("Set MUSIC_FILE in .env to a licensed audio track")
    license_name = os.getenv("MUSIC_LICENSE", "").strip()
    if not license_name:
        raise RuntimeError("Set MUSIC_LICENSE in .env to document the soundtrack rights")
    attribution = os.getenv("MUSIC_ATTRIBUTION", "").strip()
    source_path = Path(configured_path).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"MUSIC_FILE does not exist: {source_path}")

    metadata = probe_media(source_path)
    if not any(stream.get("codec_type") == "audio" for stream in metadata["streams"]):
        raise ValueError(f"MUSIC_FILE contains no audio stream: {source_path}")

    cue = storyboard["music_cues"][0]
    source_hash = _file_hash(source_path)
    cache_key = compute_hash({
        "stage": "music",
        "cue": cue,
        "source_sha256": source_hash,
        "license": license_name,
        "attribution": attribution,
    })
    suffix = source_path.suffix.lower() or ".audio"
    output_path = stage_dir / f"{cue['id']}_{cache_key}{suffix}"
    if not output_path.exists():
        temporary_path = output_path.with_name(f".{output_path.name}.tmp")
        try:
            shutil.copyfile(source_path, temporary_path)
            temporary_path.replace(output_path)
        finally:
            temporary_path.unlink(missing_ok=True)
        log_run({
            "stage": "music",
            "provider": "local-file",
            "cue_id": cue["id"],
            "cache_key": cache_key,
            "model": "licensed-user-supplied-track",
            "parameters": {
                "source_filename": source_path.name,
                "source_sha256": source_hash,
                "license": license_name,
                "attribution": attribution or None,
                "start_sec": cue["start_sec"],
                "end_sec": cue["end_sec"],
            },
            "seed": None,
            "latency_sec": None,
            "cost_usd": 0.0,
            "success": True,
            "output_path": str(output_path),
        })

    return {cue["id"]: str(output_path)}
