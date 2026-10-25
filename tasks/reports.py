"""Aggregate statistics over a task list."""
from collections import Counter
from datetime import date

from .models import Priority, Status, Task


def count_by_status(tasks: list[Task]) -> dict[str, int]:
    counter = Counter(task.status.value for task in tasks)
    return dict(counter)


def overdue_tasks(tasks: list[Task], today: date | None = None) -> list[Task]:
    today = today or date.today()
    return [task for task in tasks if task.is_overdue(today)]


def completion_rate(tasks: list[Task]) -> float:
    if not tasks:
        return 0.0
    done = sum(1 for task in tasks if task.status == Status.DONE)
    return round(done / len(tasks) * 100, 1)


def tasks_by_tag(tasks: list[Task]) -> dict[str, list[Task]]:
    grouped: dict[str, list[Task]] = {}
    for task in tasks:
        for tag in task.tags:
            grouped.setdefault(tag, []).append(task)
    return grouped


def urgency(task: Task, today: date) -> str:
    """Triage label for reports: how soon a task needs attention."""
    if task.status == Status.DONE:
        return "none"
    if task.is_overdue(today):
        return "critical"
    if task.priority == Priority.HIGH:
        return "high"
    if task.priority == Priority.MEDIUM:
        return "normal"
    return "low"
