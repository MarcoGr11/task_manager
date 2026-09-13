from datetime import date

from tasks.models import Priority, Status, Task


def test_mark_done_changes_status():
    task = Task(id=1, title="Write report")
    task.mark_done()
    assert task.status == Status.DONE


def test_is_overdue_true_for_past_due_date_not_done():
    task = Task(id=2, title="Old task", due_date=date(2020, 1, 1))
    assert task.is_overdue(date(2024, 1, 1)) is True


def test_is_overdue_false_when_done():
    task = Task(id=3, title="Done task", due_date=date(2020, 1, 1), status=Status.DONE)
    assert task.is_overdue(date(2024, 1, 1)) is False


def test_add_tag_normalizes_and_dedupes():
    task = Task(id=4, title="Tagged")
    task.add_tag("  Work ")
    task.add_tag("work")
    assert task.tags == ["work"]


def test_round_trip_dict():
    task = Task(id=5, title="Roundtrip", priority=Priority.HIGH, due_date=date(2025, 5, 1))
    restored = Task.from_dict(task.to_dict())
    assert restored == task
