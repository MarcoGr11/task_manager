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
        lines = []
        for t in tasks:
            if args.status is not None:
                if t.status.value != args.status:
                    continue
            if args.priority is not None:
                if t.priority.name != args.priority:
                    continue
            if args.tag is not None:
                if args.tag.strip().lower() not in t.tags:
                    continue
            if args.overdue:
                if not t.is_overdue(date.today()):
                    continue
            if t.priority == Priority.HIGH:
                marker = "!!!"
            elif t.priority == Priority.MEDIUM:
                marker = "!"
            else:
                marker = ""
            line = f"#{t.id} [{t.status.value}] {t.title}"
            if marker:
                line = f"{line} {marker}"
            if t.due_date is not None:
                if t.is_overdue(date.today()):
                    line = f"{line} (OVERDUE since {t.due_date.isoformat()})"
                else:
                    line = f"{line} (due {t.due_date.isoformat()})"
            lines.append(line)
        if not lines:
            return "No tasks match the filters."
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
