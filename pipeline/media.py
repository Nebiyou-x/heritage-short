import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _tool(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(f"{name} is required but was not found on PATH")
    return executable


def require_ffmpeg_filters(required: set[str]) -> None:
    result = subprocess.run(
        [_tool("ffmpeg"), "-hide_banner", "-filters"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Unable to inspect FFmpeg filters:\n{result.stderr[-4000:]}")
    available = set(re.findall(r"^\s*[.A-Z]{3}\s+([a-z0-9_]+)\s", result.stdout, re.MULTILINE))
    missing = sorted(required - available)
    if missing:
        raise RuntimeError(f"FFmpeg is missing required filters: {', '.join(missing)}")


def require_ffmpeg_encoders(required: set[str]) -> None:
    result = subprocess.run(
        [_tool("ffmpeg"), "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Unable to inspect FFmpeg encoders:\n{result.stderr[-4000:]}")
    available = set(re.findall(r"^\s*[A-Z.]{6}\s+([a-z0-9_]+)\s", result.stdout, re.MULTILINE))
    missing = sorted(required - available)
    if missing:
        raise RuntimeError(f"FFmpeg is missing required encoders: {', '.join(missing)}")


def run_ffmpeg(arguments: list[str]) -> None:
    result = subprocess.run(
        [_tool("ffmpeg"), "-hide_banner", "-nostdin", "-y", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-6000:]}")


def probe_media(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            _tool("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Unable to inspect media {path}:\n{result.stderr[-4000:]}")
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid metadata for {path}") from exc
    if not metadata.get("streams"):
        raise ValueError(f"No media streams found in {path}")
    return metadata


def verify_video(
    path: Path,
    expected_duration: float,
    width: int,
    height: int,
    require_audio: bool = True,
) -> None:
    metadata = probe_media(path)
    video_streams = [stream for stream in metadata["streams"] if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in metadata["streams"] if stream.get("codec_type") == "audio"]
    if not video_streams or (require_audio and not audio_streams):
        requirement = "video and audio" if require_audio else "video"
        raise ValueError(f"Export must contain {requirement} streams: {path}")
    video = video_streams[0]
    if video.get("width") != width or video.get("height") != height:
        raise ValueError(
            f"Export has resolution {video.get('width')}x{video.get('height')}; "
            f"expected {width}x{height}"
        )
    try:
        duration = float(metadata["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Export has no valid duration: {path}") from exc
    if abs(duration - expected_duration) > 0.5:
        raise ValueError(
            f"Export duration is {duration:.2f}s; expected about {expected_duration:.2f}s"
        )
