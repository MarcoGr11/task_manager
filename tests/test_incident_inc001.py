"""Regression tests for INC-001 (docs/incidents/inc-001.md): notifier outage and concurrent task creation."""
import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import respx
from fastapi.testclient import TestClient

from tasks import api, notifier_resilient
from tasks.notifier_resilient import NOTIFIER_URL, notify_task_created
from tasks.storage import TaskStorage


@respx.mock
def test_undelivered_notification_is_kept_for_replay(monkeypatch, tmp_path):
    """INC-001: 163 notifications were dropped for good during the outage (no outbox)."""
    monkeypatch.setattr(notifier_resilient.time, "sleep", lambda _: None)
    monkeypatch.setenv("NOTIFIER_OUTBOX", str(tmp_path / "outbox.jsonl"))
    respx.post(NOTIFIER_URL).mock(side_effect=httpx.ConnectError("Connection refused"))

    assert notify_task_created({"id": 42, "title": "x"})["delivered"] is False

    outbox = tmp_path / "outbox.jsonl"
    assert outbox.exists(), "undelivered notification must be persisted for replay"
    assert [json.loads(line)["id"] for line in outbox.read_text().splitlines()] == [42]


@respx.mock
def test_delivery_outcome_is_exported_as_metric(monkeypatch, tmp_path):
    """INC-001: /metrics had no notifier series, so no alert could fire."""
    monkeypatch.setattr(notifier_resilient.time, "sleep", lambda _: None)
    monkeypatch.setenv("NOTIFIER_OUTBOX", str(tmp_path / "outbox.jsonl"))
    respx.post(NOTIFIER_URL).mock(return_value=httpx.Response(503))
    notify_task_created({"id": 1, "title": "x"})

    metrics = TestClient(api.app).get("/metrics").text

    assert 'notifier_delivery_total{result="fallback"}' in metrics


def test_concurrent_creates_do_not_lose_tasks(monkeypatch, tmp_path):
    """INC-001 side finding: 667 x 201 but only 547 tasks stored (lost updates in load-modify-save)."""
    monkeypatch.setattr(api, "storage", TaskStorage(tmp_path / "tasks.json"))
    monkeypatch.setattr(api, "notify_task_created", lambda task: {"delivered": True, "attempts": 1})

    with ThreadPoolExecutor(max_workers=16) as pool:
        ids = list(pool.map(lambda i: api.create_task(api.TaskIn(title=f"t{i}"))["id"], range(200)))

    stored = api.storage.load()
    assert len(set(ids)) == 200, "every 201 must carry its own id"
    assert len(stored) == 200, "every acknowledged task must be stored"
