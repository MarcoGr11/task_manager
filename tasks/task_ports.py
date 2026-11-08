"""Abstract ports between the task services and their infrastructure."""
from typing import Protocol

from .consent import Consent
from .models import Task


class TaskReader(Protocol):
    def load(self) -> list[Task]: ...


class TaskStore(TaskReader, Protocol):
    def save(self, tasks: list[Task]) -> None: ...

    def next_id(self, tasks: list[Task]) -> int: ...


class ConsentStore(Protocol):
    def load(self) -> list[Consent]: ...

    def save(self, items: list[Consent]) -> None: ...


class ConsentChecker(Protocol):
    def allowed(self, user_id: int, purpose: str) -> bool: ...


class TaskPublisher(Protocol):
    def __call__(self, task: dict) -> dict: ...
