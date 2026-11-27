"""JSON-file backed persistence for tasks."""
import json
import os
from pathlib import Path

from .models import Task


class TaskStorage:
    """Loads and saves a list of Task objects to a JSON file."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [Task.from_dict(item) for item in raw]

    def save(self, tasks: list[Task]) -> None:
        data = [task.to_dict() for task in tasks]
        # CAPA CA-3 (INC-001): write a temp file and swap it in, so a concurrent load never sees a truncated file.
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def next_id(self, tasks: list[Task]) -> int:
        if not tasks:
            return 1
        return max(task.id for task in tasks) + 1
