"""Outbox for notifications the notifier did not accept (CAPA CA-2, ADR-0005).

The API appends a task here after the retry budget is spent; nothing is lost while the notifier is down.
Replay is manual on purpose (CCB condition C3: receiver idempotency is not confirmed):
    python -m tasks.notifier_outbox replay     # prints "delivered=<n> left=<n>", exit 1 if anything is left
    python -m tasks.notifier_outbox pending    # prints the number of waiting notifications
"""
import json
import os
import sys
import threading
from pathlib import Path

import httpx

_lock = threading.Lock()  # one writer per process; replay works on a renamed file, so processes do not collide


def outbox_path() -> Path:
    return Path(os.getenv("NOTIFIER_OUTBOX", "notifications_outbox.jsonl"))


def append(task: dict) -> None:
    with _lock, outbox_path().open("a", encoding="utf-8") as outbox:
        outbox.write(json.dumps(task) + "\n")


def pending() -> list[dict]:
    path = outbox_path()
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line] if path.exists() else []


def replay() -> tuple[int, int]:
    """Send every waiting notification once; keep the ones that fail. Returns (delivered, left)."""
    from .notifier_resilient import NOTIFIER_URL, TIMEOUT_SECONDS  # late import: notifier_resilient imports us

    path = outbox_path()
    if not path.exists():
        return 0, 0
    work = path.with_name(path.name + ".replaying")
    os.replace(path, work)  # fallbacks that happen during replay go to a fresh outbox file
    delivered, left = 0, []
    for task in [json.loads(line) for line in work.read_text(encoding="utf-8").splitlines() if line]:
        try:
            httpx.post(NOTIFIER_URL, json=task, timeout=TIMEOUT_SECONDS).raise_for_status()
            delivered += 1
        except httpx.HTTPError:
            left.append(task)
    for task in left:
        append(task)
    work.unlink()
    return delivered, len(left)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "pending"
    if command == "replay":
        sent, waiting = replay()
        print(f"delivered={sent} left={waiting}")
        sys.exit(1 if waiting else 0)
    print(f"pending={len(pending())}")
