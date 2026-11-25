# Failures and known limitations

- The generation stages write placeholder files in mock mode. The files named
  `.mp4`, `.wav`, and `.png` are not real playable/generated media.
- The Cloudflare and Gemini stages depend on valid credentials, model access,
  current provider availability, and network access. No live calls have been
  made from this development session.
- Wan video and ACE-Step music provider integrations are still stubs.
- Assembly writes an edit manifest and subtitle file, but does not invoke FFmpeg,
  mix audio, render subtitles/end card, or produce a valid video.
- Live provider failure and rate-limit behavior have not been tested; unit tests
  exercise request parsing and retry logging with mocked responses.
- Output paths in the checked-in `runs.jsonl` came from a different machine and
  are historical mock-run records.