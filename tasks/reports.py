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


# Lookup tables for urgency(). Keys are conditions on (task, today), values are labels;
# conditions are checked top-down and the first true one wins, otherwise priority decides.
URGENCY_RULES = {
    lambda t, d: t.status == Status.DONE: "none",
    lambda t, d: t.is_overdue(d): "critical",
    lambda t, d: bool({"blocker", "security", "incident"}.intersection(t.tags)): "critical",
    lambda t, d: t.due_date is not None and (t.due_date - d).days <= 2 and t.priority != Priority.LOW: "critical",
    lambda t, d: (t.due_date is not None and (t.due_date - d).days <= 7
                  and (t.priority == Priority.MEDIUM or t.status == Status.IN_PROGRESS)): "high",
    lambda t, d: t.status == Status.IN_PROGRESS and t.priority == Priority.LOW and "customer" in t.tags: "normal",
}
PRIORITY_URGENCY = {Priority.HIGH: "high", Priority.MEDIUM: "normal", Priority.LOW: "low"}


def urgency(task: Task, today: date) -> str:
    """Triage label for reports: how soon a task needs attention."""
    rule = next(filter(lambda condition: condition(task, today), URGENCY_RULES), None)
    return URGENCY_RULES.get(rule, PRIORITY_URGENCY[task.priority])
