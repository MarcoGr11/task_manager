"""Domain model for a single task."""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Task:
    """A single task tracked by the task manager."""

    id: int
    title: str
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    due_date: date | None = None
    tags: list[str] = field(default_factory=list)

    def is_overdue(self, today: date) -> bool:
        if self.due_date is None:
            return False
        return self.status != Status.DONE and self.due_date < today

    def mark_done(self) -> None:
        self.status = Status.DONE

    def add_tag(self, tag: str) -> None:
        normalized = tag.strip().lower()
        if normalized and normalized not in self.tags:
            self.tags.append(normalized)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority.name,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        due = date.fromisoformat(data["due_date"]) if data.get("due_date") else None
        return Task(
            id=data["id"],
            title=data["title"],
            priority=Priority[data.get("priority", "MEDIUM")],
            status=Status(data.get("status", "todo")),
            due_date=due,
            tags=list(data.get("tags", [])),
        )
