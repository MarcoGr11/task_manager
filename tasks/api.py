"""HTTP API for the task manager."""
import logging
import os
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .consent import ConsentStorage
from .logging_utils import install_sensitive_data_filter
from .models import Priority, Task
from .notifier_resilient import notify_task_created
from .privacy import build_export
from .storage import TaskStorage
from .user import User, hash_password
from .user_storage import UserStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
install_sensitive_data_filter()  # central PII/secret sanitizer for all loggers
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


def correlation_id(x_correlation_id: str | None = Header(default=None)) -> str:
    return x_correlation_id or uuid.uuid4().hex


def authorize_subject(actor_id: int, subject_id: int, corr_id: str, action: str, allow_admin: bool = False):
    """Actor must BE the subject (or an admin where allowed). Same 403 for a foreign id and
    for an id that does not exist, so the response never reveals whether a profile exists."""
    users = user_storage.load()
    subject = user_storage.find(users, subject_id)
    actor = user_storage.find(users, actor_id)
    is_admin = allow_admin and actor is not None and actor.is_admin
    if subject is None or (actor_id != subject_id and not is_admin):
        logger.warning("access_denied action=%s actor_id=%s subject_id=%s correlation_id=%s",
                       action, actor_id, subject_id, corr_id)
        raise HTTPException(status_code=403, detail="Forbidden")
    return users, subject


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
    logger.info(f"User registered: id={user.id} email={user.email} phone={user.phone}")
    return {"id": user.id}


@app.get("/api/users/{user_id}/personal-data")
def export_personal_data(
    user_id: int, actor_id: int = Depends(current_user_id), corr_id: str = Depends(correlation_id)
) -> dict:
    _, user = authorize_subject(actor_id, user_id, corr_id, "personal_data_export")
    export = build_export(user, storage.load(), consent_storage.load())
    # Audit the fact only: never the exported JSON itself.
    logger.info("personal_data_export result=success actor_id=%s subject_id=%s correlation_id=%s",
                actor_id, user_id, corr_id)
    return export
