# Costs

No external model calls or paid media-generation jobs have been run by the
current implementation. Mock entries in `runs.jsonl` report `$0.00` because
they incur no provider usage; they must not be used to estimate production cost.

Before a real run, verify current provider pricing, quotas, model availability,
and licensing. Keep per-call usage and billing data in `runs.jsonl`; separately
track GPU time and any local infrastructure costs.