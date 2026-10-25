from datetime import date

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
