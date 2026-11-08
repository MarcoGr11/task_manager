"""Task services tested on in-memory ports; one test wires the real storages."""
from datetime import date, timedelta

import pytest

from tasks.consent import ConsentStorage
from tasks.models import Status, Task
from tasks.storage import TaskStorage
from tasks.task_services import ConsentService, NotificationDispatcher, ReportExporter, TaskService

TODAY = date(2026, 11, 8)
PURPOSE = "MARKETING_EMAIL"


class FakeTaskStore:
    def __init__(self):
        self.items: list[Task] = []

    def load(self):
        return list(self.items)

    def save(self, tasks):
        self.items = list(tasks)

    def next_id(self, tasks):
        return len(tasks) + 1


class FakeConsentStore:
    def __init__(self):
        self.items = []

    def load(self):
        return list(self.items)

    def save(self, items):
        self.items = list(items)


class FakeConsents:
    def __init__(self, *allowed_users):
        self.allowed_users = allowed_users

    def allowed(self, user_id, purpose):
        return user_id in self.allowed_users


class FakePublisher:
    def __init__(self):
        self.calls = []

    def __call__(self, task):
        self.calls.append(task)
        return {"delivered": True, "attempts": 1}


@pytest.fixture
def store():
    return FakeTaskStore()


@pytest.fixture
def service(store):
    return TaskService(store)


def overdue_task(task_id=1, owner_id=None):
    return Task(task_id, "late", due_date=TODAY - timedelta(days=1), owner_id=owner_id)


def test_create_assigns_sequential_ids(service):
    assert [service.create("a").id, service.create("b").id] == [1, 2]


def test_complete_removes_task_from_open(service):
    task = service.create("a")
    assert service.complete(task.id).status == Status.DONE
    assert service.list_open() == []


def test_unknown_task_returns_none(service):
    assert service.complete(9) is None and service.add_tag(9, "x") is None


def test_add_tag_is_normalized(service):
    task = service.create("a")
    service.add_tag(task.id, " Urgent ")
    assert service.list_open()[0].tags == ["urgent"]


def test_unknown_consent_purpose_is_rejected():
    with pytest.raises(ValueError):
        ConsentService(FakeConsentStore()).grant(1, "NOPE")


def test_grant_then_revoke_changes_allowed():
    consents = ConsentService(FakeConsentStore())
    consents.grant(1, PURPOSE)
    assert consents.allowed(1, PURPOSE)
    consents.revoke(1, PURPOSE)
    assert not consents.allowed(1, PURPOSE)


@pytest.mark.parametrize("owner_id", [None, 2])
def test_no_notification_without_owner_or_consent(owner_id):
    publisher = FakePublisher()
    assert NotificationDispatcher(publisher, FakeConsents(1)).notify_created(Task(1, "a", owner_id=owner_id)) is None
    assert publisher.calls == []


def test_notification_sanitizes_recorded_title():
    publisher = FakePublisher()
    record = NotificationDispatcher(publisher, FakeConsents(1)).notify_created(
        Task(1, "write alice@example.com", owner_id=1))
    assert len(publisher.calls) == 1
    assert record["delivered"] and "alice@example.com" not in record["title"]


def test_notify_overdue_only_contactable_owners():
    publisher = FakePublisher()
    tasks = [overdue_task(1, owner_id=1), overdue_task(2, owner_id=2), overdue_task(3), Task(4, "ok", owner_id=1)]
    records = NotificationDispatcher(publisher, FakeConsents(1)).notify_overdue(tasks, TODAY)
    assert [r["task_id"] for r in records] == [1]


def test_summary_and_overdue(store):
    store.items = [overdue_task(1), Task(2, "done", status=Status.DONE)]
    exporter = ReportExporter(store)
    assert exporter.summary(TODAY) == {"completion_rate": 50.0, "by_status": {"todo": 1, "done": 1}, "overdue": 1}
    assert [t.id for t in exporter.overdue(TODAY)] == [1]


def test_urgency_map_marks_overdue_critical(store):
    store.items = [overdue_task(1)]
    assert ReportExporter(store).urgency_map(TODAY) == {1: "critical"}


def test_csv_has_header_and_sanitized_rows(store):
    store.items = [Task(1, "mail alice@example.com")]
    lines = ReportExporter(store).to_csv(TODAY).splitlines()
    assert lines[0] == "id,title,status,urgency"
    assert len(lines) == 2 and "alice@example.com" not in lines[1]


def test_services_work_with_real_storages(tmp_path):
    task_store = TaskStorage(tmp_path / "tasks.json")
    consents = ConsentService(ConsentStorage(tmp_path / "consents.json"))
    consents.grant(1, PURPOSE)
    publisher = FakePublisher()
    task = TaskService(task_store).create("real", owner_id=1)
    assert NotificationDispatcher(publisher, consents).notify_created(task)["delivered"]
    assert [t.title for t in task_store.load()] == ["real"]
