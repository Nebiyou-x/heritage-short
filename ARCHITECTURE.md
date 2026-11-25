# Architecture

- **Contract (`storyboard.json` + `schema/storyboard.schema.json`):** Validated
  with JSON Schema before every run. Semantic validation also checks the 60–90
  second runtime, unique shot and cue IDs, and continuous music coverage.
- **Stages (`pipeline/stages/`):** `keyframes`, `shots`, `music`, `narration`,
  and `assemble` have independent stage boundaries and write beneath `outputs/`.
  Keyframes can call Cloudflare Workers AI (FLUX.1 Schnell); narration can call
  Gemini 3.8 Flash TTS. Wan video, ACE-Step music, and playable-media assembly
  are not implemented yet.
- **Caching:** Generation stages hash their stage inputs and reuse matching
  outputs. Cache hits currently do not append a model-call log entry because
  there was no model call.
- **Retries & logging:** The shared retry helper retries failures up to three
  times with linear backoff. Connected provider stages log each attempt,
  parameters, seed where supported, latency, success/failure, and output path to
  `runs.jsonl`. Costs are `null` for live calls until reliable usage/billing data
  is connected.
- **Mock mode:** `USE_MOCK=1` exercises the stage flow only. Placeholder files
  are not valid generated video, audio, or imagery. The full pipeline rejects
  `USE_MOCK=0` to avoid starting paid generation before all stages are ready.
  `pipeline.run_stage` is the supported entry point for running the two connected
  provider stages individually.