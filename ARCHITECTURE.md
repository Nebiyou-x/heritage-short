# Architecture

- **Contract (`storyboard.json` + `schema/storyboard.schema.json`):** Validated before every run using `jsonschema`.
- **Stages (`pipeline/stages/`):** `keyframes`, `shots`, `music`, `narration`, and `assemble` read `storyboard.json` and write deterministic outputs under `outputs/`.
- **Caching:** Each unit computes a SHA-256 hash over its stage-specific inputs; unchanged items reuse existing outputs without re-calling models.
- **Retries & Logging:** Transient errors retry up to 3 times with backoff; every model/stage execution appends a structured JSON record to `runs.jsonl`.