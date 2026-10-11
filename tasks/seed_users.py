"""Create synthetic demo users with tasks. All values are fictional (example.com, fake phones).

Usage: python -m tasks.seed_users   (writes users.json, tasks.json, empty consents.json)
"""
import os
import secrets
from pathlib import Path

from .consent import ConsentStorage
from .models import Priority, Task
from .storage import TaskStorage
from .user import User, hash_password
from .user_storage import UserStorage

USERS = [
    User(1, "Alice Example", "alice@example.com", "+380501234567", hash_password("demo-pass-alice"),
         reset_token=secrets.token_urlsafe(16)),
    User(2, "Bob Sample", "bob@example.com", "+380671112233", hash_password("demo-pass-bob"), None),
    User(3, "Admin Demo", "admin@example.com", "+380931234500", hash_password("demo-pass-admin"), None,
         is_admin=True),
]
TASKS = [
    Task(1, "Prepare sprint review", Priority.HIGH, owner_id=1),
    Task(2, "Buy office supplies", Priority.LOW, owner_id=1, tags=["office"]),
    Task(3, "Fix login bug", Priority.HIGH, owner_id=2),
    Task(4, "Write release notes", owner_id=2),
    Task(5, "Rotate demo keys", owner_id=3),
]

UserStorage(Path(os.getenv("USERS_DB", "users.json"))).save(USERS)
TaskStorage(Path(os.getenv("TASKS_DB", "tasks.json"))).save(TASKS)
ConsentStorage(Path(os.getenv("CONSENTS_DB", "consents.json"))).save([])
print(f"Seeded {len(USERS)} users, {len(TASKS)} tasks")
