import base64
import os
from typing import Any

import requests


CLOUDFLARE_IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"
GEMINI_TTS_MODEL = "gemini-3.8-flash-tts"


def is_retryable_provider_error(exc: Exception) -> bool:
    if isinstance(exc, requests.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        return status in {408, 425, 429} or (status is not None and status >= 500)
    return isinstance(exc, (requests.Timeout, requests.ConnectionError))


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def generate_cloudflare_image(prompt: str, seed: int) -> bytes:
    account_id = _required_env("CLOUDFLARE_ACCOUNT_ID")
    token = _required_env("CLOUDFLARE_API_TOKEN")
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
        f"/ai/run/{CLOUDFLARE_IMAGE_MODEL}"
    )
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": prompt, "seed": seed, "steps": 4},
        timeout=120,
    )
    response.raise_for_status()
    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"Cloudflare Workers AI request failed: {body.get('errors', [])}")
    image = body.get("result", {}).get("image")
    if not isinstance(image, str):
        raise ValueError("Cloudflare Workers AI response did not contain a generated image")
    image_bytes = base64.b64decode(image, validate=True)
    if not image_bytes.startswith(b"\xff\xd8"):
        raise ValueError("Cloudflare Workers AI returned an image that is not JPEG data")
    return image_bytes


def generate_gemini_speech(
    text: str,
    voice: str,
    style: str,
) -> bytes:
    api_key = _required_env("GEMINI_API_KEY")
    body: dict[str, Any] = {
        "model": GEMINI_TTS_MODEL,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": text,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": style,
                }],
            }],
        }],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        headers={"x-goog-api-key": api_key},
        json=body,
        timeout=120,
    )
    response.raise_for_status()
    response_body = response.json()
    for step in reversed(response_body.get("steps", [])):
        if step.get("type") != "model_output":
            continue
        for content in step.get("content", []):
            if content.get("type") == "audio" and isinstance(content.get("data"), str):
                audio = base64.b64decode(content["data"], validate=True)
                if audio.startswith(b"RIFF") and audio[8:12] == b"WAVE":
                    return audio
                raise ValueError("Gemini TTS response did not contain WAV audio")
    raise ValueError("Gemini TTS response did not contain generated audio")
