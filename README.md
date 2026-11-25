# Heritage Short

A storyboard-driven Python pipeline for producing a short, narrated film in
horizontal (16:9) and vertical (9:16) formats. The sample story is a fictional
Amharic family comedy. The pipeline combines Cloudflare-generated keyframes,
Gemini text-to-speech narration, FFmpeg Ken Burns motion, a locally supplied
licensed music track, English subtitles, and an AI disclosure end card.

The storyboard is the source of truth for shot order, duration, prompts, spoken
text, subtitles, seeds, and score timing. The current edit is a motion-illustrated
film made from still images; it does not generate character animation or
cinematic video clips.

## Requirements

- Python 3.10 or later (the project uses standard library typing features).
- FFmpeg and `ffprobe`, with the `libx264` and AAC encoders and the `scale`,
  `crop`, `zoompan`, `subtitles`, `sidechaincompress`, `loudnorm`, and audio
  filters used by the mixer.
- Cloudflare Workers AI credentials for production keyframes.
- A Gemini API key with access to Gemini 3.8 Flash TTS.
- One local audio file for the licensed soundtrack.

Install the Python dependencies:

```sh
python -m pip install -r requirements.txt
```

Check FFmpeg and `ffprobe` are available on `PATH`:

```sh
ffmpeg -version
ffprobe -version
```

The production preflight checks required credentials, the soundtrack's audio
stream, FFmpeg filters, and encoders before it starts any model generation.

## Configure production

Copy the example environment file and edit the copy:

```sh
cp .env.example .env
```

Set these values in `.env`:

```dotenv
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
GEMINI_API_KEY=...
MUSIC_FILE=/absolute/path/to/licensed-track.wav
MUSIC_LICENSE=license name or written permission
```

Optionally set `MUSIC_ATTRIBUTION`, `GEMINI_TTS_VOICE`, and
`GEMINI_TTS_STYLE`. Keep `.env` private; it is ignored by Git. Never paste
provider secrets into source files, commits, logs, or chat. `MUSIC_LICENSE` is
for documenting the track's rights; it does not establish that the track is
licensed.

Set billing limits or alerts directly in the Cloudflare and Google provider
consoles before running. The pipeline does not enforce a dollar budget, and it
does not yet receive billable usage totals from either provider. The approved
$10 smoke-test budget is not a hard cap enforced by this code.

## Commands

Validate the JSON Schema and storyboard timing contract:

```sh
make validate
```

Exercise the local stage plumbing without calling model APIs:

```sh
make mock-film
```

Mock mode writes placeholders and an edit manifest only. It deliberately does
not produce files named as if they were playable videos.

Run the full production pipeline after configuring credentials, soundtrack,
licensing details, and provider billing limits:

```sh
make film
```

`make film` forces the Cloudflare and Gemini providers and turns mock mode off.
It generates any uncached keyframes and narration, creates motion shots for
both aspect ratios, mixes the audio, and writes verified MP4s beneath `outputs/`.
Provider generation is billable and sends the corresponding prompts or
narration text to those providers. Cache hits reuse existing assets.

Provider stages can also be run individually:

```sh
KEYFRAMES_PROVIDER=cloudflare make keyframes
NARRATION_PROVIDER=gemini make narration
```

## Pipeline contract and outputs

The storyboard must satisfy [`schema/storyboard.schema.json`](schema/storyboard.schema.json)
and the additional checks in `pipeline/validate.py`: unique shot/cue IDs,
continuous score coverage, and a final runtime of 60–90 seconds including the
four-second end card.

The supplied storyboard has eight shots totaling 69 seconds; the completed
timeline is 73 seconds with the end card. The assembler targets 1920×1080 at
24 fps for 16:9 and 1080×1920 at 24 fps for 9:16. Each still receives a subtle
Ken Burns zoom. English subtitles are burned into the story portion; Amharic
narration is mixed with the soundtrack, which is ducked under speech.

Outputs include:

- `outputs/keyframes/` — cached generated or mock keyframes.
- `outputs/shots/` — per-shot MP4s for each aspect ratio in production.
- `outputs/narration/` — cached WAV narration in production.
- `outputs/music/` — a cached copy of the supplied track in production.
- `outputs/subtitles_*.srt` — timed English subtitles.
- `outputs/edit_manifest_*.json` — input/output references, timing, license
  details, and audio settings.
- `outputs/film_16x9_*.mp4` and `outputs/film_9x16_*.mp4` — final exports,
  verified for video/audio streams, dimensions, and duration.
- `runs.jsonl` — append-only records for generation, render, and failure
  attempts. Live provider costs remain `null` until usage billing is integrated.

## Tests and review

Run the unit tests with:

```sh
python -m unittest discover -s tests -v
```

The tests cover storyboard checks, provider request/response parsing with
mocked HTTP responses, stage logging, mock export behavior, and local track
handling. A short local FFmpeg integration render has also been checked in both
aspect ratios. No live Cloudflare or Gemini requests have been made from this
development session.

Before delivery, watch and listen to both complete exports. Verify Amharic
pronunciation, subtitle meaning/timing, image composition in each crop, music
rights, and the final disclosure. Structural media checks cannot judge those
creative or cultural details.

## Project documentation

- [Architecture](ARCHITECTURE.md) — stage boundaries, data flow, cache and logs.
- [Design](DESIGN.md) — story, visual/audio direction, and delivery intent.
- [Experiments](EXPERIMENTS.md) — what has and has not been tested.
- [Failures and limitations](FAILURES.md) — known gaps and operational risks.
- [Costs](COSTS.md) — billing assumptions and cost-accounting limitations.
- [Ethics and consent](ETHICS.md) — likeness, privacy, licensing, and disclosure.
