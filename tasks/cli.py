"""Minimal command-line interface for the task manager."""
import argparse
from datetime import date
from pathlib import Path

from .models import Priority, Task
from .reports import completion_rate, count_by_status, overdue_tasks
from .storage import TaskStorage

DEFAULT_DB = Path("tasks.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasks")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a new task")
    add.add_argument("title")
    add.add_argument("--priority", choices=[p.name for p in Priority], default="MEDIUM")

    sub.add_parser("list", help="List all tasks")
    sub.add_parser("stats", help="Show summary statistics")

    done = sub.add_parser("done", help="Mark a task as done")
    done.add_argument("task_id", type=int)

    return parser


def run(args: argparse.Namespace, storage: TaskStorage) -> str:
    tasks = storage.load()

    if args.command == "add":
        task = Task(
            id=storage.next_id(tasks),
            title=args.title,
            priority=Priority[args.priority],
        )
        tasks.append(task)
        storage.save(tasks)
        return f"Added task #{task.id}: {task.title}"

    if args.command == "list":
        if not tasks:
            return "No tasks yet."
        lines = [f"#{t.id} [{t.status.value}] {t.title}" for t in tasks]
        return "\n".join(lines)

    if args.command == "stats":
        by_status = count_by_status(tasks)
        overdue = overdue_tasks(tasks, date.today())
        rate = completion_rate(tasks)
        return (
            f"Completion rate: {rate}%\n"
            f"By status: {by_status}\n"
            f"Overdue: {len(overdue)}"
        )

    if args.command == "done":
        for task in tasks:
            if task.id == args.task_id:
                task.mark_done()
                storage.save(tasks)
                return f"Task #{task.id} marked done."
        return f"Task #{args.task_id} not found."

    return "Unknown command."


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    storage = TaskStorage(DEFAULT_DB)
    print(run(args, storage))


if __name__ == "__main__":
    main()
