# Experiments and validation

This log separates deliberate experiments from validation and operational
troubleshooting. Live Cloudflare and Gemini requests were made and their
latencies are present in `runs.jsonl`; that operational evidence is summarized
below. The existing notes do not document ten planned, controlled experiments
with hypotheses and comparisons, and no model quality scores or Amharic voice
evaluations are available. Do not count unplanned provider failures as
experiments.

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

## Observed production-run measurements

The current-workspace production records in `runs.jsonl` show eight successful
Cloudflare FLUX.1 Schnell keyframe requests (30.999 seconds total; median
1.965 seconds), followed by 16 successful local FFmpeg shot renders for the two
aspect ratios (270.135 seconds total; median 16.377 seconds). Eight successful
Gemini 3.8 Flash TTS requests took 46.476 seconds total (median 5.620 seconds).
The two final FFmpeg assemblies took 147.687 and 159.637 seconds. The local
music-copy record has no measured latency. These are elapsed request/process
times from this run, not GPU time or model-quality measurements.

The log also contains four failed Cloudflare HTTP attempts before the eight
successful keyframes, and five failed Gemini HTTP attempts before the eight
successful narration outputs. The accompanying reflection identifies the
Cloudflare errors as an authorization-scope failure and an unsupported request
field, and the Gemini errors as HTTP 429 quota/rate limiting. Provider costs
are `null`; the logs do not establish whether failed attempts were billable.

These are run measurements, not controlled experiments: no hypothesis,
systematic prompt comparison, human rating, or fixed-seed comparison was
recorded. GPU minutes are absent for every production stage.

## Existing run log

The first entries in the committed `runs.jsonl` are historical mock executions
whose output paths refer to another machine. Mock entries showing `$0.00`
describe local placeholders only. Later records include real provider calls
from this workspace, but still do not contain provider-reported billing usage.

## Production experiments still needed

For future controlled experiments:

1. Make one keyframe request and inspect the returned image before generating
   the full set.
2. Synthesize one Amharic line, measure its duration, and have a fluent speaker
   review pronunciation, tone, and text fidelity.
3. If both samples are acceptable, run the full storyboard under provider-side
   billing limits; record request IDs/usage if available, actual spend from the
   provider consoles, latency, settings, and human ratings.
4. Watch and listen to both complete aspect-ratio exports, then note cropping,
   subtitle readability/timing, voice/music balance, and any revisions.

Record each actual experiment's date, hypothesis, one changed variable, fixed
seed and other settings, cache key, model/version, output path, measured
difference, reason for the choice, and human evaluation where relevant. Include
failed and inconclusive results. Do not copy secrets or private prompt data
into this file. The ten-entry rubric is not yet met; add entries only for tests
that were actually run.
