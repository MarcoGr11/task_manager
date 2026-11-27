from fastapi.testclient import TestClient

from tasks import api, notifier_resilient
from tasks.models import Priority, Task
from tasks.storage import TaskStorage


def test_get_task_by_id(monkeypatch, tmp_path):
    store = TaskStorage(tmp_path / "tasks.json")
    store.save([Task(1, "A"), Task(2, "B", priority=Priority.HIGH)])
    monkeypatch.setattr(api, "storage", store)
    client = TestClient(api.app)

    assert client.get("/tasks/2").json()["priority"] == "HIGH"
    assert client.get("/tasks/99").status_code == 404


def test_notifier_timeout_default():
    assert notifier_resilient.TIMEOUT_SECONDS == 1.0
