"""Behaviour of the TaskHub facade, including notifications gated by consent."""
from datetime import date, timedelta

import pytest

from tasks import task_hub
from tasks.models import Status
from tasks.task_hub import TaskHub

TODAY = date(2026, 11, 8)
PURPOSE = "MARKETING_EMAIL"


@pytest.fixture
def published(monkeypatch):
    calls = []

    def fake_notify(payload):
        calls.append(payload)
        return {"delivered": True, "attempts": 1}

    monkeypatch.setattr(task_hub, "notify_task_created", fake_notify)
    return calls


@pytest.fixture
def hub(tmp_path, published):
    return TaskHub(tmp_path / "tasks.json", tmp_path / "consents.json")


def test_create_assigns_sequential_ids_and_persists(hub):
    assert [hub.create_task("a").id, hub.create_task("b").id] == [1, 2]
    assert [t.title for t in hub.list_open()] == ["a", "b"]


def test_complete_task_removes_it_from_open(hub):
    task = hub.create_task("a")
    assert hub.complete_task(task.id).status == Status.DONE
    assert hub.list_open() == []


def test_complete_unknown_task_returns_none(hub):
    assert hub.complete_task(99) is None


def test_add_tag_is_normalized_and_persisted(hub):
    task = hub.create_task("a")
    hub.add_tag(task.id, " Urgent ")
    assert hub.list_open()[0].tags == ["urgent"]


def test_unknown_consent_purpose_is_rejected(hub):
    with pytest.raises(ValueError):
        hub.grant_consent(1, "NOPE")


def test_grant_then_revoke_changes_contactability(hub):
    hub.grant_consent(1, PURPOSE)
    assert hub.can_contact(1)
    hub.revoke_consent(1, PURPOSE)
    assert not hub.can_contact(1)


def test_owner_without_consent_is_not_notified(hub, published):
    hub.create_task("a", owner_id=1)
    assert published == []


def test_ownerless_task_is_not_notified(hub, published):
    hub.create_task("a")
    assert published == [] and not hub.can_contact(None)


def test_owner_with_consent_is_notified_and_title_sanitized(hub, published):
    hub.grant_consent(1, PURPOSE)
    hub.create_task("write alice@example.com", owner_id=1)
    assert len(published) == 1
    assert "alice@example.com" not in hub.sent[0]["title"]


def _overdue(hub, owner_id):
    task = hub.create_task("late", owner_id=owner_id)
    tasks = hub.tasks.load()
    tasks[0].due_date = TODAY - timedelta(days=1)
    hub.tasks.save(tasks)
    return task


def test_notify_overdue_counts_only_contactable(hub, published):
    _overdue(hub, 2)
    assert hub.notify_overdue(TODAY) == 0
    hub.grant_consent(2, PURPOSE)
    assert hub.notify_overdue(TODAY) == 1


def test_summary_counts(hub):
    _overdue(hub, None)
    done = hub.create_task("done")
    hub.complete_task(done.id)
    assert hub.summary(TODAY) == {"completion_rate": 50.0, "by_status": {"todo": 1, "done": 1}, "overdue": 1}


def test_urgency_map_marks_overdue_critical(hub):
    task = _overdue(hub, None)
    assert hub.urgency_map(TODAY) == {task.id: "critical"}


def test_export_csv_writes_header_and_rows(hub, tmp_path):
    hub.create_task("a")
    target = tmp_path / "out.csv"
    assert hub.export_csv(target, TODAY) == 1
    assert target.read_text(encoding="utf-8").splitlines() == ["id,title,status,urgency", "1,a,todo,normal"]
