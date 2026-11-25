# Experiments and validation

This log separates local pipeline checks from provider quality experiments. No
live Cloudflare or Gemini requests have been made from this development session;
therefore there are no measured provider costs, provider latencies, model
quality scores, or Amharic voice evaluations to report.

## Completed checks

| Check | Setup | Result | What it establishes |
|---|---|---|---|
| Storyboard validation | Checked `storyboard.json` against the schema and semantic timeline rules. | Passed. The eight story shots total 69 seconds; adding the four-second end card gives 73 seconds. | The checked-in sample satisfies the current machine-checkable contract. |
| Unit tests | `python -m unittest discover -s tests -v` | 19 tests passed. | Covers validation, provider payload/response parsing using mocked HTTP responses, retry logging, mock export behavior, music file handling, cache invalidation for subtitles, and narration overrun rejection. |
| Production preflight | Local temporary WAV and dummy credential strings; no provider request was made. | Passed with the installed FFmpeg build. | Confirms local audio probing plus required filter and encoder discovery. It does not authenticate provider credentials. |
| FFmpeg end-to-end smoke render | Temporary one-image, one-shot, three-second fixture with silent WAV voice/music; real FFmpeg, both target aspect ratios. | Produced and ffprobe-verified a seven-second export at 1920×1080 and 1080×1920, including subtitle/end-card composition and an audio stream. Temporary files were removed. | Exercises local rendering and stream validation only; it is not a representative film or model-generated asset. |
| Missing-credential guard | Invoked `make film` with no `.env` configured. | Stopped in production preflight before model requests. | Confirms that absent credentials prevent the paid generation sequence from starting. |

The temporary render used placeholder visual/audio content and is not included in
the repository. No claims about composition, sound quality, Amharic speech,
provider availability, or provider billing follow from this check.

## Existing run log

The committed `runs.jsonl` contains historical mock executions whose output
paths refer to another machine. They are retained as sample records, not treated
as evidence of a current production run. Mock entries showing `$0.00` describe
local placeholders only.

## Production experiments still needed

After credentials and the licensed soundtrack are configured:

1. Make one keyframe request and inspect the returned image before generating
   the full set.
2. Synthesize one Amharic line, measure its duration, and have a fluent speaker
   review pronunciation, tone, and text fidelity.
3. If both samples are acceptable, run the full storyboard under provider-side
   billing limits; record request IDs/usage if available, actual spend from the
   provider consoles, latency, settings, and human ratings.
4. Watch and listen to both complete aspect-ratio exports, then note cropping,
   subtitle readability/timing, voice/music balance, and any revisions.

Record a real experiment's date, cache key, model/version, parameters, seed,
provider outcome, output path, measured latency, provider-reported usage/cost,
and human evaluation. Do not copy secrets or private prompt data into this
file. Update the record with failures as well as successful outputs.
