import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = ROOT_DIR / "outputs"
RUNS_LOG_PATH = ROOT_DIR / "runs.jsonl"


def ensure_dirs() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:16]


def log_run(entry: Dict[str, Any]) -> None:
    ensure_dirs()
    entry_with_ts = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    with RUNS_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry_with_ts, ensure_ascii=False) + "\n")


def run_with_retry(
    fn: Callable[[], Any],
    retries: int = 3,
    backoff_sec: float = 1.5,
    on_retry: Callable[[int, Exception], None] | None = None,
    should_retry: Callable[[Exception], bool] | None = None,
) -> Any:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                if should_retry is not None and not should_retry(exc):
                    raise
                if on_retry:
                    on_retry(attempt, exc)
                time.sleep(backoff_sec * attempt)
    assert last_err is not None
    raise last_err


def run_logged_generation(
    fn: Callable[[], Any],
    entry: Dict[str, Any],
    retries: int = 3,
    should_retry: Callable[[Exception], bool] | None = None,
) -> Any:
    attempt = 0

    def _run_attempt() -> Any:
        nonlocal attempt
        attempt += 1
        start = time.perf_counter()
        try:
            result = fn()
        except Exception as exc:
            log_run({
                **entry,
                "attempt": attempt,
                "latency_sec": round(time.perf_counter() - start, 3),
                "success": False,
                "error": type(exc).__name__,
            })
            raise
        log_run({
            **entry,
            "attempt": attempt,
            "latency_sec": round(time.perf_counter() - start, 3),
            "success": True,
        })
        return result

    return run_with_retry(
        _run_attempt,
        retries=retries,
        should_retry=should_retry,
    )


def is_mock_mode() -> bool:
    return os.getenv("USE_MOCK", "1").strip() == "1"