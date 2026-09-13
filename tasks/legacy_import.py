"""Import tasks from a legacy CSV-ish export format.

NOTE: written in a hurry, needs cleanup.
"""
import json
from pathlib import Path

from .models import Priority, Status, Task


# --- Violation 1: near-duplicate of TaskStorage.load/save (Code Duplication) ---

def load_tasks_from_json(path):
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    result = []
    for item in raw:
        due = None
        if item.get("due_date"):
            from datetime import date
            due = date.fromisoformat(item["due_date"])
        result.append(
            Task(
                id=item["id"],
                title=item["title"],
                priority=Priority[item.get("priority", "MEDIUM")],
                status=Status(item.get("status", "todo")),
                due_date=due,
                tags=list(item.get("tags", [])),
            )
        )
    return result


def save_tasks_to_json(path, tasks):
    p = Path(path)
    data = []
    for task in tasks:
        data.append(
            {
                "id": task.id,
                "title": task.title,
                "priority": task.priority.name,
                "status": task.status.value,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "tags": task.tags,
            }
        )
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


# --- Violation 2: deeply nested, high Cognitive Complexity function ---

def classify_row(row, strict_mode, allow_empty_title, default_priority):
    if row is not None:
        if "title" in row:
            if row["title"] or allow_empty_title:
                if "priority" in row:
                    if row["priority"] in ("LOW", "MEDIUM", "HIGH"):
                        priority = row["priority"]
                    else:
                        if strict_mode:
                            raise ValueError("bad priority")
                        else:
                            priority = default_priority
                else:
                    priority = default_priority
                if "status" in row:
                    if row["status"] in ("todo", "in_progress", "done"):
                        status = row["status"]
                    else:
                        if strict_mode:
                            raise ValueError("bad status")
                        else:
                            status = "todo"
                else:
                    status = "todo"
                if "tags" in row:
                    if isinstance(row["tags"], list):
                        tags = row["tags"]
                    else:
                        if strict_mode:
                            raise ValueError("bad tags")
                        else:
                            tags = []
                else:
                    tags = []
                return {"priority": priority, "status": status, "tags": tags}
            else:
                if strict_mode:
                    raise ValueError("empty title")
                else:
                    return None
        else:
            if strict_mode:
                raise ValueError("missing title")
            else:
                return None
    else:
        return None


# --- Violation 3: security hotspot / vulnerability (use of eval on external input) ---

def run_migration_expression(expr, context):
    """Evaluate a small filter expression from a legacy config file."""
    return eval(expr, {"__builtins__": {}}, context)  # noqa: S307
