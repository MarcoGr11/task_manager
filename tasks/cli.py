"""Minimal command-line interface for the task manager."""
import argparse
from datetime import date
from pathlib import Path

from .models import Priority, Status, Task
from .reports import completion_rate, count_by_status, overdue_tasks
from .storage import TaskStorage

DEFAULT_DB = Path("tasks.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasks")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a new task")
    add.add_argument("title")
    add.add_argument("--priority", choices=[p.name for p in Priority], default="MEDIUM")

    lst = sub.add_parser("list", help="List tasks (optionally filtered)")
    lst.add_argument("--status", choices=[s.value for s in Status])
    lst.add_argument("--priority", choices=[p.name for p in Priority])
    lst.add_argument("--tag")
    lst.add_argument("--overdue", action="store_true")
    sub.add_parser("stats", help="Show summary statistics")

    done = sub.add_parser("done", help="Mark a task as done")
    done.add_argument("task_id", type=int)

    return parser


PRIORITY_MARKERS = {Priority.HIGH: " !!!", Priority.MEDIUM: " !", Priority.LOW: ""}


def _matches(task: Task, args: argparse.Namespace, today: date) -> bool:
    if args.status is not None and task.status.value != args.status:
        return False
    if args.priority is not None and task.priority.name != args.priority:
        return False
    if args.tag is not None and args.tag.strip().lower() not in task.tags:
        return False
    return not args.overdue or task.is_overdue(today)


def _format_line(task: Task, today: date) -> str:
    line = f"#{task.id} [{task.status.value}] {task.title}{PRIORITY_MARKERS[task.priority]}"
    if task.due_date is None:
        return line
    if task.is_overdue(today):
        return f"{line} (OVERDUE since {task.due_date.isoformat()})"
    return f"{line} (due {task.due_date.isoformat()})"


def _cmd_add(args: argparse.Namespace, storage: TaskStorage, tasks: list[Task]) -> str:
    task = Task(id=storage.next_id(tasks), title=args.title, priority=Priority[args.priority])
    tasks.append(task)
    storage.save(tasks)
    return f"Added task #{task.id}: {task.title}"


def _cmd_list(args: argparse.Namespace, storage: TaskStorage, tasks: list[Task]) -> str:
    if not tasks:
        return "No tasks yet."
    today = date.today()
    lines = [_format_line(t, today) for t in tasks if _matches(t, args, today)]
    return "\n".join(lines) or "No tasks match the filters."


def _cmd_stats(args: argparse.Namespace, storage: TaskStorage, tasks: list[Task]) -> str:
    return (
        f"Completion rate: {completion_rate(tasks)}%\n"
        f"By status: {count_by_status(tasks)}\n"
        f"Overdue: {len(overdue_tasks(tasks, date.today()))}"
    )


def _cmd_done(args: argparse.Namespace, storage: TaskStorage, tasks: list[Task]) -> str:
    task = next((t for t in tasks if t.id == args.task_id), None)
    if task is None:
        return f"Task #{args.task_id} not found."
    task.mark_done()
    storage.save(tasks)
    return f"Task #{task.id} marked done."


COMMANDS = {"add": _cmd_add, "list": _cmd_list, "stats": _cmd_stats, "done": _cmd_done}


def run(args: argparse.Namespace, storage: TaskStorage) -> str:
    handler = COMMANDS.get(args.command)
    if handler is None:
        return "Unknown command."
    return handler(args, storage, storage.load())


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    storage = TaskStorage(DEFAULT_DB)
    print(run(args, storage))


if __name__ == "__main__":
    main()
