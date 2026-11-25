import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from pipeline.common import ensure_dirs, is_mock_mode
from pipeline.media import probe_media, require_ffmpeg_encoders, require_ffmpeg_filters
from pipeline.validate import validate_storyboard
from pipeline.stages.keyframes import run_keyframes_stage
from pipeline.stages.shots import run_shots_stage
from pipeline.stages.music import run_music_stage
from pipeline.stages.narration import run_narration_stage
from pipeline.stages.assemble import run_assemble_stage


def _preflight() -> None:
    required = (
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_API_TOKEN",
        "GEMINI_API_KEY",
        "MUSIC_LICENSE",
    )
    missing = [
        name
        for name in required
        if not os.getenv(name, "").strip()
        or os.getenv(name, "").strip().lower().startswith("your_")
        or os.getenv(name, "").strip() == "describe-the-license-or-permission"
    ]
    if missing:
        raise RuntimeError("Production run needs these .env values: " + ", ".join(missing))

    music_file = os.getenv("MUSIC_FILE", "").strip()
    if not music_file:
        raise RuntimeError("Set MUSIC_FILE in .env to the licensed soundtrack file")
    music_path = Path(music_file).expanduser().resolve()
    if not music_path.is_file():
        raise FileNotFoundError(f"MUSIC_FILE does not exist: {music_path}")
    metadata = probe_media(music_path)
    if not any(stream.get("codec_type") == "audio" for stream in metadata["streams"]):
        raise ValueError(f"MUSIC_FILE contains no audio stream: {music_path}")

    require_ffmpeg_filters({
        "scale",
        "crop",
        "zoompan",
        "subtitles",
        "sidechaincompress",
        "loudnorm",
        "aresample",
        "aformat",
        "apad",
        "atrim",
        "adelay",
        "amix",
        "asplit",
        "afade",
        "volume",
    })
    require_ffmpeg_encoders({"libx264", "aac"})


def main() -> None:
    load_dotenv()
    ensure_dirs()
    parser = argparse.ArgumentParser(description="Generate and assemble the Heritage Short.")
    parser.add_argument("storyboard", nargs="?", type=Path, default=Path("storyboard.json"))
    parser.add_argument(
        "schema",
        nargs="?",
        type=Path,
        default=Path("schema/storyboard.schema.json"),
    )
    args = parser.parse_args()

    storyboard = validate_storyboard(args.storyboard, args.schema)
    if not is_mock_mode():
        _preflight()

    music = run_music_stage(storyboard)
    keyframes = run_keyframes_stage(storyboard)
    shots = run_shots_stage(storyboard, keyframes)
    narration = run_narration_stage(storyboard)
    exports = run_assemble_stage(storyboard, keyframes, shots, music, narration)

    if is_mock_mode():
        print("Mock pipeline complete. No playable exports were rendered.")
    else:
        print("Pipeline complete. Verified exports:")
        for aspect_ratio, path in exports.items():
            print(f"  [{aspect_ratio}] {path}")


if __name__ == "__main__":
    main()