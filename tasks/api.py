"""HTTP API for the task manager."""
import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .models import Priority, Task
from .notifier_resilient import notify_task_created
from .storage import TaskStorage

storage = TaskStorage(Path(os.getenv("TASKS_DB", "tasks.json")))
app = FastAPI(title="Task Manager API")


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
