"""Monolithic facade over tasks, consents, notifications, reports and export (Lab 8 audit baseline)."""
import csv
import io
from datetime import date
from pathlib import Path

from .consent import PURPOSES, Consent, ConsentStorage
from .consent_policy import check_consent, grant, revoke
from .logging_utils import sanitize_text
from .models import Priority, Status, Task
from .notifier_resilient import notify_task_created
from .privacy import now_iso
from .reports import completion_rate, count_by_status, overdue_tasks, urgency
from .storage import TaskStorage

NOTIFICATION_PURPOSE = "MARKETING_EMAIL"
CONSENT_SOURCE = "task_hub"


class TaskHub:
    def __init__(self, tasks_path: Path, consents_path: Path):
        self.tasks = TaskStorage(tasks_path)
        self.consents = ConsentStorage(consents_path)
        self.sent: list[dict] = []

    def create_task(self, title: str, priority: str = "MEDIUM", owner_id: int | None = None) -> Task:
        tasks = self.tasks.load()
        task = Task(self.tasks.next_id(tasks), title, Priority[priority], owner_id=owner_id)
        tasks.append(task)
        self.tasks.save(tasks)
        self.notify_created(task)
        return task

    def complete_task(self, task_id: int) -> Task | None:
        tasks = self.tasks.load()
        task = next((t for t in tasks if t.id == task_id), None)
        if task is not None:
            task.mark_done()
            self.tasks.save(tasks)
        return task

    def add_tag(self, task_id: int, tag: str) -> Task | None:
        tasks = self.tasks.load()
        task = next((t for t in tasks if t.id == task_id), None)
        if task is not None:
            task.add_tag(tag)
            self.tasks.save(tasks)
        return task

    def list_open(self) -> list[Task]:
        return [t for t in self.tasks.load() if t.status != Status.DONE]

    def grant_consent(self, user_id: int, purpose: str) -> Consent:
        if purpose not in PURPOSES:
            raise ValueError(f"unknown purpose: {purpose}")
        updated, record, _ = grant(self.consents.load(), user_id, purpose, CONSENT_SOURCE)
        self.consents.save(list(updated))
        return record

    def revoke_consent(self, user_id: int, purpose: str) -> Consent | None:
        updated, record, _ = revoke(self.consents.load(), user_id, purpose, CONSENT_SOURCE)
        self.consents.save(updated)
        return record

    def can_contact(self, user_id: int | None) -> bool:
        return user_id is not None and check_consent(user_id, NOTIFICATION_PURPOSE, self.consents.load())

    def notify_created(self, task: Task) -> bool:
        if not self.can_contact(task.owner_id):
            return False
        result = notify_task_created(task.to_dict())
        self.sent.append({"task_id": task.id, "title": sanitize_text(task.title), "at": now_iso(), **result})
        return True

    def notify_overdue(self, today: date) -> int:
        return sum(self.notify_created(t) for t in overdue_tasks(self.tasks.load(), today))

    def summary(self, today: date) -> dict:
        tasks = self.tasks.load()
        return {
            "completion_rate": completion_rate(tasks),
            "by_status": count_by_status(tasks),
            "overdue": len(overdue_tasks(tasks, today)),
        }

    def urgency_map(self, today: date) -> dict[int, str]:
        return {t.id: urgency(t, today) for t in self.tasks.load()}

    def export_csv(self, target: Path, today: date) -> int:
        tasks = self.tasks.load()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "title", "status", "urgency"])
        writer.writerows([t.id, sanitize_text(t.title), t.status.value, urgency(t, today)] for t in tasks)
        Path(target).write_text(buffer.getvalue(), encoding="utf-8")
        return len(tasks)
