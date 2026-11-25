# Architecture

## System overview

The pipeline is a local, command-line Python application. It has no web server,
database, task queue, hosted service, or automatic cloud deployment. The
storyboard is the central production contract; each stage consumes the
storyboard and cached assets, then returns paths for the next stage.

```text
                         storyboard.json + schema
                                  |
                               validate
                             /          \
                            v            v
       keyframes (Cloudflare FLUX)      narration (Gemini TTS)
                    |                         |
                    v                         |
       shots (FFmpeg Ken Burns)               |
                    |                         |
                    +------------+------------+
                                 |
local licensed track -> music stage (rights record + cached copy)
                                 |
                                 v
          assembly (subtitles, ducked score, end card)
                                 |
                                 v
                verified MP4s + manifest + run log
```

The production orchestration entry point is `pipeline/run.py`. The
`make film` target validates the storyboard, performs a local preflight, then
runs the stages in order. `pipeline/run_stage.py` supports running only the
keyframe or narration provider stage. `make mock-film` exercises the stages
without sending provider requests and does not create playable MP4 files.

## Storyboard contract

`storyboard.json` is checked against `schema/storyboard.schema.json` with
Draft 2020-12 JSON Schema validation. The schema covers required fields,
shot/music item shapes, duration bounds per shot, supported aspect ratios, and
seed types. Semantic validation in `pipeline/validate.py` additionally checks:

- The final runtime, including the shared four-second AI end card, is 60–90
  seconds.
- Shot IDs and music cue IDs are unique.
- Music begins at time zero, has no gaps, and covers the complete shot timeline.
- Schema errors are reported with their JSON paths before any generation starts.

The current sample has eight shots totaling 69 seconds and one music cue that
covers those shots. The final export is 73 seconds after the end card.

## Stages and artifacts

All generated or staged files live below `outputs/`; per-item cache keys are
derived from canonical JSON inputs by `pipeline/common.py`. A matching cached
file is reused without another generation request.

### Music input

In production, `MUSIC_FILE` points to one local soundtrack. The stage uses
`ffprobe` to verify it contains audio, hashes the source, copies it into
`outputs/music/`, and records the declared `MUSIC_LICENSE` plus optional
`MUSIC_ATTRIBUTION`. It does not generate music, edit cue boundaries, or
validate legal ownership. The production assembler currently accepts exactly
one continuous cue.

### Keyframes

`pipeline/stages/keyframes.py` builds a prompt from the global style block,
character description, and shot image prompt. The Cloudflare Workers AI
REST request uses `@cf/black-forest-labs/flux-1-schnell`, the storyboard seed,
and four inference steps. The response is checked as JPEG data and cached as a
per-shot image.

Mock mode writes a tiny placeholder PNG and prompt text. A placeholder is not a
production image.

### Shots

`pipeline/stages/shots.py` turns each keyframe into one H.264 silent clip per
requested aspect ratio. FFmpeg crops to 1920×1080 (16:9) or 1080×1920 (9:16),
then applies a slow centered zoom at 24 fps. Production outputs use `libx264`,
the configured `FFMPEG_PRESET`/`FFMPEG_CRF` or defaults `medium`/`20`, and
`yuv420p`.

This is motion applied to a still image, not video generation. Storyboard
`motion_prompt` text is not currently interpreted by the Ken Burns renderer.

### Narration

`pipeline/stages/narration.py` submits each shot's Amharic transcript to the
Gemini Interactions API using `gemini-3.8-flash-tts`. The voice and delivery
style are configurable with `GEMINI_TTS_VOICE` and `GEMINI_TTS_STYLE`; the
default voice is `Kore`. The response must contain WAV data. The stage checks
that each resulting audio duration fits its shot, allowing a small 0.25-second
tolerance; it fails rather than silently trimming an overlong line.

English subtitles come directly from the storyboard and are not sent as
narration text.

### Assembly

`pipeline/stages/assemble.py` concatenates per-aspect shot clips, burns the
English SRT subtitles into the story, and appends a four-second black disclosure
card. It pads/positions each narration clip on the shot timeline, loops/trims
the supplied music, fades the music near the end of the story, and applies an
FFmpeg sidechain compressor so the score ducks under speech. The final mix is
normalized to −14 LUFS with a −1 dB true-peak target and encoded as AAC.

The output is written to a temporary path and only renamed to the final MP4
after `ffprobe` verifies video and audio streams, expected dimensions, and
duration. The SRT and edit manifest are written next to the exports.

## Preflight, caching, retries, and logging

Before any model calls, the production preflight checks required environment
values, the music file and its audio stream, required FFmpeg filters, and
`libx264`/AAC encoders. It does not contact the providers to test credentials.

Cloudflare and Gemini requests retry at most three times for timeouts,
connection errors, HTTP 408/425/429, and HTTP 5xx responses. Other HTTP failures
are surfaced without retries. Each attempt is recorded to `runs.jsonl` with
timestamp, provider/model, request parameters, cache key, seed when available,
latency, outcome, and output path. Live API `cost_usd` is `null`: neither
provider billing usage is currently integrated. Cached requests produce no new
model-call entry because no model request occurred.

FFmpeg stages are local and are logged separately. Mock generation records
zero cost because no provider service was called. The committed historical
`runs.jsonl` contains mock runs from another machine and is not a production
cost or reproducibility record.

## Configuration and security

Secrets belong in the ignored local `.env`, never in the storyboard, committed
documentation, or run log. Production prompts and Amharic transcripts are sent
to the configured providers; avoid including private family details. The
pipeline copies a soundtrack into `outputs/`, so the working directory should
have appropriate access controls and enough disk space.

The runner does not implement a hard dollar cap, provider usage accounting,
cloud job queue, distributed locking, or automatic cleanup of cached assets.
Set account-side spending limits and manage output retention explicitly.
