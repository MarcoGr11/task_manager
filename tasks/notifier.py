"""Client for the external notification service (baseline: no retry, no fallback)."""
import os

import httpx

NOTIFIER_URL = os.getenv("NOTIFIER_URL", "http://localhost:9100/notify")


def notify_task_created(task: dict) -> dict:
    """Send a notification; any network or HTTP error propagates to the caller."""
    response = httpx.post(NOTIFIER_URL, json=task)
    response.raise_for_status()
    return {"delivered": True}
