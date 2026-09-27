"""Client for the external notification service with Retry + Fallback."""
import logging
import os
import random
import time

import httpx

NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://localhost:9100/notify")

# Resilience parameters, rationale in README_LAB2.md.
MAX_ATTEMPTS = 3  # 1 call + 2 retries: bounded, so a failing notifier is never flooded
BASE_DELAY_SECONDS = 0.2  # exponential backoff: 0.2s, then 0.4s
MAX_JITTER_SECONDS = 0.1  # spreads retries of concurrent clients apart
TIMEOUT_SECONDS = 1.0  # per attempt; worst case ~3 * 1.0 + 0.6 + 0.2 = 3.8s

logger = logging.getLogger(__name__)
_rng = random.SystemRandom()


def _is_retryable(error: httpx.HTTPError) -> bool:
    """Retry only transient failures: timeouts, connection errors, HTTP 5xx."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code >= 500
    return isinstance(error, httpx.TransportError)


def backoff_delay(attempt: int) -> float:
    return BASE_DELAY_SECONDS * 2 ** (attempt - 1) + _rng.uniform(0, MAX_JITTER_SECONDS)


def notify_task_created(task: dict) -> dict:
    """Send a notification; if the notifier keeps failing, degrade instead of raising."""
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        try:
            response = httpx.post(NOTIFIER_URL, json=task, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return {"delivered": True, "attempts": attempt}
        except httpx.HTTPError as error:
            logger.warning("Notifier attempt %d/%d failed: %r", attempt, MAX_ATTEMPTS, error)
            if not _is_retryable(error):
                break
            if attempt < MAX_ATTEMPTS:
                time.sleep(backoff_delay(attempt))
    logger.error("Notifier unavailable, fallback used for task %s", task.get("id"))
    return {"delivered": False, "attempts": attempt}
