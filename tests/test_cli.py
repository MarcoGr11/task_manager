"""Characterization tests for cli.run, written before the Lab 3 refactoring."""
from datetime import date

from tasks.cli import build_parser, run
from tasks.models import Priority, Status, Task
from tasks.storage import TaskStorage

PAST = date(2000, 1, 1)
FUTURE = date(2999, 1, 1)


def make_storage(tmp_path, tasks):
    storage = TaskStorage(tmp_path / "tasks.json")
    storage.save(tasks)
    return storage


def cli(storage, *argv):
    return run(build_parser().parse_args(argv), storage)


def sample():
    return [
        Task(id=1, title="Low", priority=Priority.LOW, tags=["home"]),
        Task(id=2, title="Mid", priority=Priority.MEDIUM, status=Status.DONE, due_date=PAST),
        Task(id=3, title="High", priority=Priority.HIGH, due_date=PAST, tags=["work"]),
        Task(id=4, title="Later", priority=Priority.HIGH, status=Status.IN_PROGRESS, due_date=FUTURE),
    ]


def test_list_formats_markers_and_due_dates(tmp_path):
    out = cli(make_storage(tmp_path, sample()), "list")
    assert out.splitlines() == [
        "#1 [todo] Low",
        "#2 [done] Mid ! (due 2000-01-01)",
        "#3 [todo] High !!! (OVERDUE since 2000-01-01)",
        "#4 [in_progress] Later !!! (due 2999-01-01)",
    ]


def test_list_empty_storage(tmp_path):
    assert cli(make_storage(tmp_path, []), "list") == "No tasks yet."


def test_list_filter_by_status(tmp_path):
    assert cli(make_storage(tmp_path, sample()), "list", "--status", "done") == "#2 [done] Mid ! (due 2000-01-01)"


def test_list_filter_by_priority(tmp_path):
    out = cli(make_storage(tmp_path, sample()), "list", "--priority", "HIGH")
    assert [line.split()[0] for line in out.splitlines()] == ["#3", "#4"]


def test_list_filter_by_tag_is_case_insensitive(tmp_path):
    assert cli(make_storage(tmp_path, sample()), "list", "--tag", " WORK ").startswith("#3 ")


def test_list_overdue_excludes_done_and_future(tmp_path):
    out = cli(make_storage(tmp_path, sample()), "list", "--overdue")
    assert out == "#3 [todo] High !!! (OVERDUE since 2000-01-01)"


def test_list_combined_filters(tmp_path):
    storage = make_storage(tmp_path, sample())
    assert cli(storage, "list", "--priority", "HIGH", "--status", "in_progress").startswith("#4 ")
    assert cli(storage, "list", "--priority", "LOW", "--tag", "work") == "No tasks match the filters."


def test_add_then_done(tmp_path):
    storage = make_storage(tmp_path, [])
    assert cli(storage, "add", "Write report", "--priority", "HIGH") == "Added task #1: Write report"
    assert cli(storage, "done", "1") == "Task #1 marked done."
    assert cli(storage, "done", "99") == "Task #99 not found."
    assert storage.load()[0].status == Status.DONE


def test_stats(tmp_path):
    out = cli(make_storage(tmp_path, sample()), "stats")
    assert out.splitlines() == [
        "Completion rate: 25.0%",
        "By status: {'todo': 2, 'done': 1, 'in_progress': 1}",
        "Overdue: 1",
    ]
