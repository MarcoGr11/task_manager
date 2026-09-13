"""Import tasks from a legacy CSV-ish export format.

Refactored: reuses TaskStorage instead of duplicating (de)serialization,
replaces the monolithic classify_row with small guard-clause helpers,
and removes the eval()-based expression evaluator.
"""
from .models import Priority, Status, Task
from .storage import TaskStorage

VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}
VALID_STATUSES = {"todo", "in_progress", "done"}

# Fix for Violation 1 (Duplication):
# load/save now simply delegate to TaskStorage instead of re-implementing
# the same (de)serialization logic a second time.


def load_tasks_from_json(path):
    return TaskStorage(path).load()


def save_tasks_to_json(path, tasks):
    TaskStorage(path).save(tasks)


# Fix for Violation 2 (Cognitive Complexity):
# classify_row is decomposed into three small, single-purpose helpers
# using Guard Clauses (early return) instead of deep nesting.


def _resolve_priority(row, strict_mode, default_priority):
    priority = row.get("priority", default_priority)
    if priority in VALID_PRIORITIES:
        return priority
    if strict_mode:
        raise ValueError("bad priority")
    return default_priority


def _resolve_status(row, strict_mode):
    status = row.get("status", "todo")
    if status in VALID_STATUSES:
        return status
    if strict_mode:
        raise ValueError("bad status")
    return "todo"


def _resolve_tags(row, strict_mode):
    tags = row.get("tags", [])
    if isinstance(tags, list):
        return tags
    if strict_mode:
        raise ValueError("bad tags")
    return []


def classify_row(row, strict_mode, allow_empty_title, default_priority):
    """Validate and normalize a raw legacy row into task field values."""
    if row is None or "title" not in row:
        if strict_mode:
            raise ValueError("missing title")
        return None

    if not row["title"] and not allow_empty_title:
        if strict_mode:
            raise ValueError("empty title")
        return None

    return {
        "priority": _resolve_priority(row, strict_mode, default_priority),
        "status": _resolve_status(row, strict_mode),
        "tags": _resolve_tags(row, strict_mode),
    }


# Fix for Violation 3 (Security Hotspot):
# eval() is removed entirely. Migration filters are now a small, explicit
# whitelist of supported comparisons instead of arbitrary code execution.

_SUPPORTED_FILTERS = {
    "status_is_done": lambda ctx: ctx.get("status") == "done",
    "priority_is_high": lambda ctx: ctx.get("priority") == "HIGH",
    "has_tags": lambda ctx: bool(ctx.get("tags")),
}


def run_migration_expression(expr, context):
    """Evaluate a named, pre-approved filter against the given context.

    Unlike the previous eval()-based implementation, this cannot execute
    arbitrary code: only expressions registered in _SUPPORTED_FILTERS
    are accepted.
    """
    if expr not in _SUPPORTED_FILTERS:
        raise ValueError(f"Unsupported migration expression: {expr!r}")
    return _SUPPORTED_FILTERS[expr](context)
