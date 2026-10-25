import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from tasks.models import Priority, Status, Task
from tasks.reports import completion_rate, count_by_status, overdue_tasks, urgency


def make_tasks():
    return [
        Task(id=1, title="A", status=Status.DONE),
        Task(id=2, title="B", status=Status.TODO, due_date=date(2020, 1, 1)),
        Task(id=3, title="C", status=Status.IN_PROGRESS),
    ]


def test_count_by_status():
    result = count_by_status(make_tasks())
    assert result["done"] == 1
    assert result["todo"] == 1


def test_completion_rate():
    assert completion_rate(make_tasks()) == 33.3


def test_completion_rate_empty():
    assert completion_rate([]) == 0.0


def test_overdue_tasks():
    overdue = overdue_tasks(make_tasks(), today=date(2024, 1, 1))
    assert len(overdue) == 1
    assert overdue[0].id == 2


TODAY = date(2024, 1, 10)


@pytest.mark.parametrize("task, expected", [
    (Task(1, "done", Priority.HIGH, Status.DONE, due_date=date(2024, 1, 1)), "none"),
    (Task(2, "late", Priority.LOW, due_date=date(2024, 1, 9)), "critical"),
    (Task(3, "high", Priority.HIGH), "high"),
    (Task(4, "medium", Priority.MEDIUM), "normal"),
    (Task(5, "low", Priority.LOW), "low"),
])
def test_urgency(task, expected):
    assert urgency(task, TODAY) == expected


# Characterization tests (Lab 6): pin the behavior of the monolithic urgency() before refactoring.
def _due(days):
    return TODAY + timedelta(days=days)


@pytest.mark.parametrize("task, expected", [
    (Task(1, "blocker", Priority.LOW, tags=["blocker"]), "critical"),
    (Task(2, "security", Priority.LOW, tags=["security"]), "critical"),
    (Task(3, "incident", Priority.LOW, tags=["incident"]), "critical"),
    (Task(4, "done blocker", Priority.LOW, Status.DONE, tags=["blocker"]), "none"),
    (Task(5, "due in 2d medium", Priority.MEDIUM, due_date=_due(2)), "critical"),
    (Task(6, "due today high", Priority.HIGH, due_date=_due(0)), "critical"),
    (Task(7, "due in 2d low", Priority.LOW, due_date=_due(2)), "low"),
    (Task(8, "due in 3d medium", Priority.MEDIUM, due_date=_due(3)), "high"),
    (Task(9, "due in 7d medium", Priority.MEDIUM, due_date=_due(7)), "high"),
    (Task(10, "due in 8d medium", Priority.MEDIUM, due_date=_due(8)), "normal"),
    (Task(11, "due in 5d low in progress", Priority.LOW, Status.IN_PROGRESS, due_date=_due(5)), "high"),
    (Task(12, "due in 5d low todo", Priority.LOW, due_date=_due(5)), "low"),
    (Task(13, "customer low in progress", Priority.LOW, Status.IN_PROGRESS, tags=["customer"]), "normal"),
    (Task(14, "customer low todo", Priority.LOW, tags=["customer"]), "low"),
    (Task(15, "customer medium in progress", Priority.MEDIUM, Status.IN_PROGRESS, tags=["customer"]), "normal"),
])
def test_urgency_rules(task, expected):
    assert urgency(task, TODAY) == expected


def test_urgency_golden_master():
    """Every status x priority x due offset x tag set, recorded from the if/elif version (commit FAIL)."""
    golden = json.loads((Path(__file__).parent / "data" / "urgency_golden.json").read_text())
    for status, priority, offset, tags, expected in golden:
        due = None if offset is None else _due(offset)
        task = Task(1, "x", Priority[priority], Status(status), due, list(tags))
        assert urgency(task, TODAY) == expected, (status, priority, offset, tags)
