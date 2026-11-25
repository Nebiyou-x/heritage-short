# Heritage Short pipeline

This repository contains a storyboard-driven pipeline scaffold for a 60–90 second
film in 16:9 and 9:16 formats. The Amharic storyboard is in `storyboard.json`;
its structure is checked against `schema/storyboard.schema.json`.

## Run

```sh
python -m pip install -r requirements.txt
make validate
make film
python -m unittest discover -s tests
```

`USE_MOCK=1` is the default. The full pipeline runs in mock mode and creates
deterministic placeholder assets; these are **not a finished or playable film**.
The keyframe and narration stages can also be run individually with real
providers:

```sh
KEYFRAMES_PROVIDER=cloudflare make keyframes
NARRATION_PROVIDER=gemini make narration
```

These calls use Cloudflare FLUX.1 Schnell and Gemini 3.8 Flash TTS, respectively.
They require the corresponding credentials below and can incur provider costs.
Successful calls and failed retry attempts are recorded in `runs.jsonl`.
`USE_MOCK=0` is rejected for the full-film command until all providers and
playable-media assembly are implemented.

Copy `.env.example` to `.env` to configure local settings. Never commit API keys.
Setting a stage's provider variable to `cloudflare` or `gemini` sends that
stage's prompt/text and related request parameters to that external provider.

## Current status

- Implemented: JSON Schema validation, film timeline checks, deterministic
  per-item cache keys, retry helper, JSONL run logging, and stage boundaries.
- Connected: Cloudflare Workers AI keyframe generation and Gemini TTS narration,
  each available as an individual stage.
- Placeholder only: Wan video generation, ACE-Step music generation, and final
  FFmpeg assembly, audio mixing/ducking, and delivery-ready exports.
- The checked-in `outputs/` files are examples from mock mode, not submission
  media. See `DESIGN.md`, `EXPERIMENTS.md`, `FAILURES.md`, and `COSTS.md` for
  current decisions and limitations.