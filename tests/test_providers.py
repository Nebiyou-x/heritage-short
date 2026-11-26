import base64
import os
import unittest
from unittest.mock import patch

import requests

from pipeline.common import run_logged_generation
from pipeline.providers import (
    CLOUDFLARE_IMAGE_MODEL,
    GEMINI_TTS_MODEL,
    generate_cloudflare_image,
    generate_gemini_speech,
    is_retryable_provider_error,
)


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class ProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {
        "CLOUDFLARE_ACCOUNT_ID": "account",
        "CLOUDFLARE_API_TOKEN": "token",
    })
    @patch("pipeline.providers.requests.post")
    def test_cloudflare_image_request_decodes_jpeg(self, post):
        jpeg = b"\xff\xd8test-image"
        post.return_value = FakeResponse({
            "success": True,
            "result": {"image": base64.b64encode(jpeg).decode("ascii")},
        })

        result = generate_cloudflare_image("warm room")

        self.assertEqual(result, jpeg)
        args, kwargs = post.call_args
        self.assertIn(CLOUDFLARE_IMAGE_MODEL, args[0])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer token")
        self.assertEqual(kwargs["json"], {"prompt": "warm room", "steps": 4})

    @patch.dict(os.environ, {
        "CLOUDFLARE_ACCOUNT_ID": "account",
        "CLOUDFLARE_API_TOKEN": "token",
    })
    @patch("pipeline.providers.requests.post")
    def test_cloudflare_rejects_non_image_payload(self, post):
        post.return_value = FakeResponse({"success": True, "result": {"image": "bm90LWpwZWc="}})
        with self.assertRaisesRegex(ValueError, "not JPEG"):
            generate_cloudflare_image("prompt")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("pipeline.providers.requests.post")
    def test_gemini_tts_request_returns_wav(self, post):
        wav = b"RIFF\x00\x00\x00\x00WAVEdata"
        post.return_value = FakeResponse({
            "steps": [{
                "type": "model_output",
                "content": [{
                    "type": "audio",
                    "data": base64.b64encode(wav).decode("ascii"),
                }],
            }],
        })

        result = generate_gemini_speech("አማርኛ", "Kore", "warm")

        self.assertEqual(result, wav)
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://generativelanguage.googleapis.com/v1beta/interactions")
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], "test-key")
        self.assertEqual(kwargs["json"]["model"], GEMINI_TTS_MODEL)
        text = kwargs["json"]["input"][0]["content"][0]
        self.assertEqual(text["text"], "አማርኛ")
        self.assertEqual(text["annotations"][0]["style"], "warm")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("pipeline.providers.requests.post")
    def test_gemini_tts_rejects_missing_audio(self, post):
        post.return_value = FakeResponse({"steps": []})
        with self.assertRaisesRegex(ValueError, "did not contain generated audio"):
            generate_gemini_speech("text", "Kore", "warm")

    @patch("pipeline.common.time.sleep")
    @patch("pipeline.common.log_run")
    def test_logged_generation_records_each_retry_attempt(self, log_run, _sleep):
        attempts = 0

        def fail_once_then_succeed():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("temporary failure")
            return b"audio"

        result = run_logged_generation(
            fail_once_then_succeed,
            {"stage": "test", "model": "fake-model", "cost_usd": None},
            retries=2,
        )

        self.assertEqual(result, b"audio")
        self.assertEqual(log_run.call_count, 2)
        self.assertFalse(log_run.call_args_list[0].args[0]["success"])
        self.assertTrue(log_run.call_args_list[1].args[0]["success"])

    def test_provider_retries_only_transient_http_errors(self):
        throttled_response = requests.Response()
        throttled_response.status_code = 429
        forbidden_response = requests.Response()
        forbidden_response.status_code = 403
        throttled = requests.HTTPError("throttled", response=throttled_response)
        forbidden = requests.HTTPError("forbidden", response=forbidden_response)

        self.assertTrue(is_retryable_provider_error(throttled))
        self.assertFalse(is_retryable_provider_error(forbidden))


if __name__ == "__main__":
    unittest.main()
