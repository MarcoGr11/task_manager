"""HTTP API for the task manager."""
import logging
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .consent import ConsentStorage
from .models import Priority, Task
from .notifier_resilient import notify_task_created
from .storage import TaskStorage
from .user import User, hash_password
from .user_storage import UserStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

storage = TaskStorage(Path(os.getenv("TASKS_DB", "tasks.json")))
user_storage = UserStorage(Path(os.getenv("USERS_DB", "users.json")))
consent_storage = ConsentStorage(Path(os.getenv("CONSENTS_DB", "consents.json")))
app = FastAPI(title="Task Manager API")


def current_user_id(x_user_id: int | None = Header(default=None)) -> int:
    """Auth STUB for the lab: X-User-Id plays the role of the logged-in principal.

    Not a production mechanism - a real service would derive the principal from a
    verified session/JWT, never from a client-supplied header.
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_user_id


class UserIn(BaseModel):
    name: str = Field(min_length=1)
    email: str
    phone: str
    password: str = Field(min_length=8)


class TaskIn(BaseModel):
    title: str = Field(min_length=1)
    priority: Priority = Priority.MEDIUM


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> list[dict]:
    return [task.to_dict() for task in storage.load()]


@app.post("/tasks", status_code=201)
def create_task(payload: TaskIn) -> dict:
    tasks = storage.load()
    task = Task(id=storage.next_id(tasks), title=payload.title, priority=payload.priority)
    tasks.append(task)
    storage.save(tasks)
    result = notify_task_created(task.to_dict())
    return {
        **task.to_dict(),
        "notification_delivered": result["delivered"],
        "notification_attempts": result["attempts"],
    }


def _validate_new_user(payload: UserIn, users: list[User]) -> None:
    if "@" not in payload.email:
        raise ValueError(f"Invalid email {payload.email}")
    if any(u.email == payload.email for u in users):
        raise ValueError(f"Email {payload.email} is already registered")


@app.post("/api/users", status_code=201)
def register_user(payload: UserIn) -> dict:
    logger.info("Register request: %s", payload.model_dump())
    users = user_storage.load()
    try:
        _validate_new_user(payload, users)
    except ValueError:
        logger.exception("Registration failed")
        raise HTTPException(status_code=422, detail="Invalid registration data")
    user = User(
        id=max((u.id for u in users), default=0) + 1,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        reset_token=None,
    )
    users.append(user)
    user_storage.save(users)
    logger.info(f"User registered: {user.email}, phone {user.phone}")
    return {"id": user.id}
