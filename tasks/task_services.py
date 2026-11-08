"""Single-responsibility task services; infrastructure is injected through the ports."""
from datetime import date

from .consent import PURPOSES, Consent
from .consent_policy import check_consent, grant, revoke
from .logging_utils import sanitize_text
from .models import Priority, Status, Task
from .privacy import now_iso
from .reports import completion_rate, count_by_status, overdue_tasks, tasks_csv, urgency
from .task_ports import ConsentChecker, ConsentStore, TaskPublisher, TaskReader, TaskStore

NOTIFICATION_PURPOSE = "MARKETING_EMAIL"
CONSENT_SOURCE = "task_services"


def _find(tasks: list[Task], task_id: int) -> Task | None:
    return next((t for t in tasks if t.id == task_id), None)


def _delivery(task: Task, result: dict) -> dict:
    return {"task_id": task.id, "title": sanitize_text(task.title), "at": now_iso(), **result}


class TaskService:
    def __init__(self, store: TaskStore):
        self._store = store

    def create(self, title: str, priority: str = "MEDIUM", owner_id: int | None = None) -> Task:
        tasks = self._store.load()
        task = Task(self._store.next_id(tasks), title, Priority[priority], owner_id=owner_id)
        tasks.append(task)
        self._store.save(tasks)
        return task

    def complete(self, task_id: int) -> Task | None:
        tasks = self._store.load()
        task = _find(tasks, task_id)
        if task is not None:
            task.mark_done()
            self._store.save(tasks)
        return task

    def add_tag(self, task_id: int, tag: str) -> Task | None:
        tasks = self._store.load()
        task = _find(tasks, task_id)
        if task is not None:
            task.add_tag(tag)
            self._store.save(tasks)
        return task

    def list_open(self) -> list[Task]:
        return [t for t in self._store.load() if t.status != Status.DONE]


class ConsentService:
    def __init__(self, store: ConsentStore):
        self._store = store

    def grant(self, user_id: int, purpose: str) -> Consent:
        if purpose not in PURPOSES:
            raise ValueError(f"unknown purpose: {purpose}")
        updated, record, _ = grant(self._store.load(), user_id, purpose, CONSENT_SOURCE)
        self._store.save(list(updated))
        return record

    def revoke(self, user_id: int, purpose: str) -> Consent | None:
        updated, record, _ = revoke(self._store.load(), user_id, purpose, CONSENT_SOURCE)
        self._store.save(updated)
        return record

    def allowed(self, user_id: int, purpose: str) -> bool:
        return check_consent(user_id, purpose, self._store.load())


class NotificationDispatcher:
    def __init__(self, publish: TaskPublisher, consents: ConsentChecker):
        self._publish = publish
        self._consents = consents

    def notify_created(self, task: Task) -> dict | None:
        if task.owner_id is None or not self._consents.allowed(task.owner_id, NOTIFICATION_PURPOSE):
            return None
        return _delivery(task, self._publish(task.to_dict()))

    def notify_overdue(self, tasks: list[Task], today: date) -> list[dict]:
        due = [t for t in overdue_tasks(tasks, today)
               if t.owner_id is not None and self._consents.allowed(t.owner_id, NOTIFICATION_PURPOSE)]
        return [_delivery(t, self._publish(t.to_dict())) for t in due]


class ReportExporter:
    def __init__(self, tasks: TaskReader):
        self._tasks = tasks

    def summary(self, today: date) -> dict:
        tasks = self._tasks.load()
        return {
            "completion_rate": completion_rate(tasks),
            "by_status": count_by_status(tasks),
            "overdue": len(overdue_tasks(tasks, today)),
        }

    def overdue(self, today: date) -> list[Task]:
        return overdue_tasks(self._tasks.load(), today)

    def urgency_map(self, today: date) -> dict[int, str]:
        return {t.id: urgency(t, today) for t in self._tasks.load()}

    def to_csv(self, today: date) -> str:
        return tasks_csv(self._tasks.load(), today)
