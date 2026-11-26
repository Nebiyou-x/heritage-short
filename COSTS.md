# Costs and budget controls

## What can incur charges

An uncached production run of the supplied eight-shot storyboard makes up to
eight Cloudflare image-generation requests and eight Gemini TTS requests. Each
provider stage retries transient request failures up to three total attempts.
If an output is already cached, its model request is skipped. A failure that
occurs after the provider has started processing may still be billable, and a
retry can create another charge.

The local FFmpeg renders, subtitle generation, soundtrack copy, and manifest
writing do not incur model-provider charges. The soundtrack itself may require
a license purchase or other payment outside this code.

## Provider pricing

Rates, free allocations, billing units, model availability, and terms can
change. Check the live provider console and pricing page immediately before
production:

- [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini text-to-speech guide](https://ai.google.dev/gemini-api/docs/speech-generation)

Cloudflare Workers AI pricing is model/usage based. Gemini TTS billing depends
on its current model and usage terms. The final amount is not safely inferred
from the number of storyboard shots alone.

## Observed timings and missing usage data

For the successful current-workspace production records in `runs.jsonl`, the
measured times were:

| Stage | Successful work recorded | Elapsed time | GPU minutes |
|---|---:|---:|---|
| Cloudflare FLUX.1 Schnell keyframes | 8 requests | 30.999 s total; 1.965 s median | Not recorded |
| FFmpeg Ken Burns shots | 16 renders (8 per aspect ratio) | 270.135 s total; 16.377 s median | Not recorded |
| Gemini 3.8 Flash TTS narration | 8 requests | 46.476 s total; 5.620 s median | Not recorded |
| FFmpeg final assembly | 2 exports | 147.687 s and 159.637 s | Not recorded |
| Local music staging | 1 copy | Latency not recorded | Not recorded |

These are elapsed wall-clock measurements, not accelerator time. The pipeline
does not report provider GPU minutes, and no defensible GPU-minute figure can
be derived from request latency. The run log also records five failed Gemini
HTTP attempts and four failed Cloudflare HTTP attempts; it does not say whether
those attempts incurred charges.

## GPU telemetry check

On November 26, 2026, a local telemetry check found no `nvidia-smi` executable.
The only exposed device was `/dev/dri/card0` using the `hyperv_drm` virtual
display driver, with no GPU activity or energy counters available. The project
uses remote Cloudflare/Gemini APIs for model stages, and its response handling
does not record provider GPU time. The eight FLUX.2 Dev responses also had no
numeric timing values in their parsed top-level `timings`/`meta` fields.
Therefore this environment cannot measure provider GPU minutes; that requires
provider-side usage data. This is an unavailable measurement, not a measured
zero.

## Image-model comparison

On November 26, 2026, eight live FLUX.2 Dev requests were run with the same
expanded storyboard prompts used by the earlier eight successful FLUX.1 Schnell
requests. Both sets produced 1024×1024 images. FLUX.1 Schnell used four steps;
FLUX.2 Dev used 25 steps and each storyboard seed. The FLUX.1 endpoint does not
accept the seed field, so this is not a same-seed comparison. The baseline
requests were logged earlier that day; the comparison was run later, not
simultaneously. Each FLUX.2 request was attempted once, without retry.

| Model | Successful images | Mean latency | Median latency | Total latency | List-price equivalent for 8 images |
|---|---:|---:|---:|---:|---:|
| FLUX.1 Schnell | 8 | 3.875 s | 1.965 s | 30.999 s | ~$0.00507* |
| FLUX.2 Dev | 8 | 13.119 s | 12.120 s | 104.951 s | ~$0.328* |

Under these settings, FLUX.2 Dev's mean latency was 3.39× the FLUX.1 Schnell
baseline, and its list-price equivalent was about 64.7× higher. These are
request latencies and rate-based equivalents, not provider GPU minutes or
actual invoice amounts.

*Pricing calculation: Cloudflare lists FLUX.1 Schnell at $0.0000528 per
512×512 tile and $0.0001056 per step. Assuming four tiles for each 1024×1024
image and additive tile and step charges, eight four-step images equal $0.0050688.
FLUX.2 Dev is listed at $0.00041 per output tile per step; eight 1024×1024
images at 25 steps equal `8 × 4 × 25 × $0.00041 = $0.328`. These figures
exclude free allocations, credits, and any billable failures; check account
usage before treating them as billed costs.

The saved comparison sheet is [outputs/benchmarks/flux2-dev-comparison.jpg](outputs/benchmarks/flux2-dev-comparison.jpg);
per-request measurements are in
[outputs/benchmarks/flux2-dev-measurements.json](outputs/benchmarks/flux2-dev-measurements.json).
A single operator's visual inspection found that the FLUX.1 images stayed
closer to the requested stylized illustration, while FLUX.2 Dev looked more
painterly/realistic. This is a subjective inspection, not a blind test, audience
rating, or proof of general model quality.

## Illustrative list-price scenario (not the actual bill)

This reproducible scenario applies the providers' published paid-tier rates
available on November 26, 2026, to the successful outputs recorded above. It
is a planning estimate, not evidence of what this project was charged.

- **Cloudflare keyframes:** The eight saved images are 1024×1024, and the
  requests use four steps each. The published FLUX.1 Schnell rates are $0.0000528
  per 512×512 tile and $0.0001056 per step. Assuming a 1024×1024 image bills as
  four tiles and that both rate components apply, the estimate is
  `8 × ((4 × $0.0000528) + (4 × $0.0001056)) = $0.0050688`.
- **Gemini TTS audio output:** The eight successful WAV files total 45.64
  seconds. At the listed standard paid rate of $0.00225 per 10 seconds of
  generated audio through December 31, 2026, the output-only estimate is
  `45.64 ÷ 10 × $0.00225 = $0.010269`. Text input is billed separately at
  $0.50 per million tokens; input token usage was not recorded and is excluded.

The resulting illustrative subtotal is **about $0.01534**, before any Gemini
text-input charge. It excludes failed/retried calls, any account free allocation
or credits, soundtrack rights, and local compute/energy. The assumption that
the Cloudflare tile and step components add as shown must be checked against
the account's usage details. This estimate must not be reported as actual
spend. Source rates: [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)
and [Gemini 3.8 Flash TTS pricing](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts).

## Logging and estimates

`runs.jsonl` records generation/render attempts, including cache key, model,
request parameters, latency, outcome, and output path. The current live
Cloudflare and Gemini entries use `cost_usd: null` because provider billing
metadata is not read from the APIs. Do not treat `null` as free, and do not use
mock records' `$0.00` as a production estimate. The scenario above is a
list-price equivalent based on explicit assumptions, not billing telemetry.
No frontier-model comparison was run or recorded.

To establish actual spend for a run:

1. Note the run time and the requests that missed cache.
2. Record provider-reported usage/request IDs if available.
3. Check both provider billing/usage dashboards after completion, including
   failed/retried calls.
4. Record the observed amount, currency, model/version, and relevant usage in
   the run report or experiment notes.

The edit manifest records the soundtrack license declaration and audio targets;
it does not assign a dollar value to the track.

## Budget controls

The user approved up to **$10 for initial smoke tests**. That is an approval,
not a code-enforced maximum. Before running `make film`, configure account-side
spending limits, quota controls, or billing alerts for both providers. This
runner cannot stop at a dollar threshold because it lacks live per-call cost
data. If a hard ceiling is required, use provider-side caps and verify that
they apply to the API keys used by this project.

Live Cloudflare and Gemini calls were made during this project, but their
actual charges are unknown from the repository. Check provider billing records
before reporting a total or claiming that the calls were free.
