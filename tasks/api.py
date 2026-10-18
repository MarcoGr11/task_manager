"""HTTP API for the task manager."""
import json
import logging
import os
import uuid
from dataclasses import asdict
from pathlib import Path

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from . import consent_policy
from .consent import PURPOSES, ConsentStorage
from .logging_utils import install_sensitive_data_filter
from .models import Priority, Task
from .notifier_resilient import notify_task_created
from .privacy import anonymize_user, build_export, now_iso
from .storage import TaskStorage
from .user import User, hash_password
from .user_storage import UserStorage, save_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
install_sensitive_data_filter()  # central PII/secret sanitizer for all loggers
logger = logging.getLogger(__name__)

storage = TaskStorage(Path(os.getenv("TASKS_DB", "tasks.json")))
user_storage = UserStorage(Path(os.getenv("USERS_DB", "users.json")))
consent_storage = ConsentStorage(Path(os.getenv("CONSENTS_DB", "consents.json")))
app = FastAPI(title="Task Manager API")
Instrumentator().instrument(app).expose(app)  # GET /metrics: request count/latency histograms

# prometheus_client's built-in process collector reads /proc (Linux only) - psutil works on macOS too.
_proc = psutil.Process()
Gauge("app_process_cpu_percent", "API process CPU, % of one core").set_function(lambda: _proc.cpu_percent(None))
Gauge("app_process_rss_bytes", "API process resident memory").set_function(lambda: _proc.memory_info().rss)


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


@app.post("/api/users/{user_id}/anonymize")
def anonymize(
    user_id: int, actor_id: int = Depends(current_user_id), corr_id: str = Depends(correlation_id)
) -> dict:
    users, user = authorize_subject(actor_id, user_id, corr_id, "anonymize", allow_admin=True)
    try:
        consents = consent_storage.load()
        changed = anonymize_user(user, consents, now_iso())
        if changed:  # one write at the end: all-or-nothing
            save_all([(user_storage, users), (consent_storage, consents)])
    except Exception:
        _audit("user_anonymized", actor_id, user_id, "failure", corr_id)
        raise HTTPException(status_code=500, detail="Anonymization failed, no changes applied")
    _audit("user_anonymized", actor_id, user_id, "success" if changed else "already_anonymized", corr_id)
    return {"subject_id": user_id, "status": "anonymized", "anonymized_at": user.anonymized_at}


def _audit(event: str, actor_id: int, subject_id: int, result: str, corr_id: str) -> None:
    """Privacy-safe audit event: ids, result, time, correlation id. Never the erased values."""
    logger.info(json.dumps({"event": event, "actor_id": actor_id, "subject_id": subject_id,
                            "result": result, "correlation_id": corr_id, "at": now_iso()}))


def _consent_command(command, user_id: int, purpose: str, actor_id: int, corr_id: str, source: str) -> dict:
    if purpose not in PURPOSES:
        raise HTTPException(status_code=422, detail=f"Unknown consent purpose, allowed: {sorted(PURPOSES)}")
    authorize_subject(actor_id, user_id, corr_id, f"consent_{command.__name__}")
    consents = consent_storage.load()
    consent, changed = command(consents, user_id, purpose, source)
    if changed:
        consent_storage.save(consents)
    _audit(f"consent_{command.__name__}", actor_id, user_id, "changed" if changed else "unchanged", corr_id)
    return asdict(consent) if consent else {"user_id": user_id, "purpose": purpose, "is_granted": False}


@app.post("/api/users/{user_id}/consents/{purpose}/grant")
def grant_consent(user_id: int, purpose: str, source: str = "api", actor_id: int = Depends(current_user_id),
                  corr_id: str = Depends(correlation_id)) -> dict:
    return _consent_command(consent_policy.grant, user_id, purpose, actor_id, corr_id, source)


@app.post("/api/users/{user_id}/consents/{purpose}/revoke")
def revoke_consent(user_id: int, purpose: str, source: str = "api", actor_id: int = Depends(current_user_id),
                   corr_id: str = Depends(correlation_id)) -> dict:
    return _consent_command(consent_policy.revoke, user_id, purpose, actor_id, corr_id, source)


def send_marketing_email(user: User) -> None:
    """Simulated side effect (no real mail server in the lab)."""
    logger.info("would send marketing email to %s", user.email)


@app.post("/api/users/{user_id}/send-marketing-email")
def marketing_email(user_id: int, actor_id: int = Depends(current_user_id),
                    corr_id: str = Depends(correlation_id)) -> dict:
    _, user = authorize_subject(actor_id, user_id, corr_id, "send_marketing_email")
    # Policy Gate right before the dependent action, with freshly loaded consents.
    if not consent_policy.check_consent(user_id, "MARKETING_EMAIL", consent_storage.load()):
        _audit("marketing_email", actor_id, user_id, "DENY", corr_id)
        raise HTTPException(status_code=403, detail="DENY: no valid consent for MARKETING_EMAIL")
    send_marketing_email(user)
    _audit("marketing_email", actor_id, user_id, "ALLOW", corr_id)
    return {"decision": "ALLOW", "sent": True}
