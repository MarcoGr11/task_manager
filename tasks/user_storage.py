"""JSON-file storage for dataclass records (users, consents)."""
import json
import os
from dataclasses import asdict
from pathlib import Path

from .user import User


class JsonStorage:
    model: type

    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list:
        if not self.path.exists():
            return []
        return [self.model(**item) for item in json.loads(self.path.read_text(encoding="utf-8"))]

    def save(self, items: list) -> None:
        save_all([(self, items)])


class UserStorage(JsonStorage):
    model = User

    def find(self, users: list[User], user_id: int) -> User | None:
        return next((u for u in users if u.id == user_id), None)


def save_all(changes: list[tuple[JsonStorage, list]]) -> None:
    """Write several files as one unit: serialize everything first, then swap files in.

    Any error while preparing data happens before a single file is touched.
    ponytail: the final os.replace calls are atomic per file, not across files;
    a real DB transaction is the upgrade path.
    """
    staged = []
    for storage, items in changes:
        tmp = storage.path.with_name(storage.path.name + ".tmp")
        tmp.write_text(json.dumps([asdict(i) for i in items], indent=2), encoding="utf-8")
        staged.append((tmp, storage.path))
    for tmp, path in staged:
        os.replace(tmp, path)
