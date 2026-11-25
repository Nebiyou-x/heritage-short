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

## Logging and estimates

`runs.jsonl` records each local generation/render attempt, including cache key,
model, request parameters, latency, success or failure, and output path. Live
provider entries currently use `cost_usd: null` because provider billing
metadata is not read from the APIs. Do not treat `null` as free, and do not use
mock records' `$0.00` as a production estimate.

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

No live provider charges have been generated from this development session.
