from datetime import date

from tasks.models import Status, Task
from tasks.reports import completion_rate, count_by_status, overdue_tasks


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
