"""Resilience tests for the notifier: httpx is mocked with respx, sleeps are recorded, not waited."""
import logging

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from tasks import api, notifier_resilient
from tasks.notifier_resilient import MAX_ATTEMPTS, NOTIFIER_URL, notify_task_created
from tasks.storage import TaskStorage

TASK = {"id": 1, "title": "Write report"}


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []
    monkeypatch.setattr(notifier_resilient.time, "sleep", recorded.append)
    return recorded


@respx.mock
def test_success_first_attempt_no_fallback(sleeps):
    route = respx.post(NOTIFIER_URL).mock(return_value=httpx.Response(200))

    assert notify_task_created(TASK) == {"delivered": True, "attempts": 1}
    assert route.call_count == 1
    assert sleeps == []


@respx.mock
def test_retry_succeeds_after_two_failures_with_backoff(sleeps):
    route = respx.post(NOTIFIER_URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200)]
    )

    assert notify_task_created(TASK) == {"delivered": True, "attempts": 3}
    assert route.call_count == 3
    assert len(sleeps) == 2
    assert 0.2 <= sleeps[0] <= 0.3
    assert 0.4 <= sleeps[1] <= 0.5


@respx.mock
def test_fallback_after_persistent_503(sleeps, caplog):
    route = respx.post(NOTIFIER_URL).mock(return_value=httpx.Response(503))

    with caplog.at_level(logging.WARNING, logger=notifier_resilient.__name__):
        result = notify_task_created(TASK)

    assert result == {"delivered": False, "attempts": MAX_ATTEMPTS}
    assert route.call_count == MAX_ATTEMPTS
    assert len(sleeps) == MAX_ATTEMPTS - 1
    assert "fallback used for task 1" in caplog.text


@respx.mock
def test_fallback_after_timeout(sleeps):
    route = respx.post(NOTIFIER_URL).mock(side_effect=httpx.ReadTimeout("timed out"))

    assert notify_task_created(TASK) == {"delivered": False, "attempts": MAX_ATTEMPTS}
    assert route.call_count == MAX_ATTEMPTS


@respx.mock
def test_client_error_is_not_retried(sleeps):
    route = respx.post(NOTIFIER_URL).mock(return_value=httpx.Response(400))

    assert notify_task_created(TASK) == {"delivered": False, "attempts": 1}
    assert route.call_count == 1
    assert sleeps == []


@respx.mock
def test_api_degrades_gracefully_when_notifier_down(sleeps, monkeypatch, tmp_path):
    monkeypatch.setattr(api, "storage", TaskStorage(tmp_path / "tasks.json"))
    respx.post(NOTIFIER_URL).mock(return_value=httpx.Response(503))

    response = TestClient(api.app).post("/tasks", json={"title": "Demo"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Demo"
    assert body["notification_delivered"] is False
    assert body["notification_attempts"] == MAX_ATTEMPTS
