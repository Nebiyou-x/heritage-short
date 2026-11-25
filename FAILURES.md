# Failures and limitations

This document distinguishes implementation limits from failures observed during
testing. No live model-provider requests have been made from this development
session, so provider-specific production failures are not yet characterized.

## Current functional limits

- **Motion is image-based.** Each output shot is an FFmpeg Ken Burns animation
  of a generated still. The storyboard's `motion_prompt` is not executed, and
  there is no Wan, Kling, or other video-generation integration.
- **Music is supplied, not generated.** Production requires one local audio
  track and a declared license. ACE-Step, multiple cues, cue transitions, and
  cue-specific edits are not implemented.
- **Amharic quality needs a human check.** The pipeline requests Gemini TTS and
  checks the returned WAV and duration, but does not assess pronunciation,
  emphasis, dialect, or whether the narration sounds natural. A fluent reviewer
  must approve it.
- **Subtitle timing is coarse.** English captions follow whole-shot timing,
  not word/sentence timestamps. There is no automatic translation or
  word-level synchronization.
- **Crops are centered.** Keyframes are center-cropped to each aspect ratio.
  The system does not detect faces or reframe around important objects.
- **One score only.** The assembler rejects more than one music cue. It loops a
  short supplied track as needed and fades near the end; it does not select
  cue regions or verify that music itself is appropriate/licensed.
- **The end card is fixed text.** It says “Made with AI / Heritage Short”; it
  is not localized or customizable in the storyboard yet.
- **Provenance is not cryptographic.** The manifest and JSONL log are ordinary
  local files. The pipeline does not generate C2PA/SynthID provenance or
  guarantee that encoders preserve metadata.

## Mock versus production

`make mock-film` writes placeholder images/text/metadata and an edit manifest
for plumbing tests. It deliberately does not create fake MP4 exports. These
placeholders are not valid generated assets and must not be submitted as a film.

The committed `runs.jsonl` is a historical mock log with paths from a different
machine. Its zero-cost entries do not represent provider pricing or current
outputs. Do not interpret it as a production audit record.

## Runtime and provider risks

- Production requires FFmpeg/ffprobe with the requested filters and encoders.
  Missing filters, fonts/subtitle support, encoders, codecs, or disk space will
  stop rendering. Preflight checks the principal filters and encoders, but
  cannot guarantee that every source file will decode.
- Cloudflare/Gemini calls require valid credentials, model access, network
  availability, quota, and current model support. The local preflight only
  checks that credential values are present; it does not authenticate them.
- Provider retries are limited to timeouts, connection errors, HTTP 408/425/429,
  and HTTP 5xx. The response may have been billed before a transient failure;
  retries can therefore incur additional charges.
- A provider may produce a valid response that is visually or vocally poor.
  Automatic format checks cannot detect quality, cultural, or content issues.
- Provider costs are logged as `null` because usage/billing details are not
  integrated. The runner does not enforce the approved dollar budget.
- Partial successful assets remain cached when a later stage fails. A rerun
  should reuse those outputs, but failed/partial files may need manual review
  before retrying.
- A custom or unsupported soundtrack format may pass basic probing but fail
  later during FFmpeg decode/mix.

## Checks completed

The current test suite covers JSON Schema and semantic validation, mocked
provider request/response behavior, retry logging, music-source checks, and
assembly-cache behavior. A short local FFmpeg render has been verified at both
target resolutions using synthetic placeholder inputs. It does not validate
live API access or the final Amharic film.

## Failure response

When a run fails:

1. Read the stage/error and attempt records in `runs.jsonl`; do not share
   credentials or private prompts when reporting it.
2. Check provider dashboards for quota, authorization, and actual charges
   before repeating model requests.
3. Keep successful cached outputs unless they are known to be corrupt; deleting
   them will require regeneration and may incur costs.
4. Fix the root cause, rerun validation, then retry only the failed stage when
   possible.
