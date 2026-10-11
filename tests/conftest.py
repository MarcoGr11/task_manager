"""Shared Lab 4 fixture: isolated JSON stores with synthetic users, tasks and consents."""
import logging

import pytest
from fastapi.testclient import TestClient

from tasks import api
from tasks.consent import Consent, ConsentStorage
from tasks.models import Task
from tasks.storage import TaskStorage
from tasks.user import User
from tasks.user_storage import UserStorage

ALICE = User(1, "Alice Example", "alice@example.com", "+380501234567",
             "pbkdf2_sha256$00$alice-synthetic-hash", "synthetic-reset-token")
BOB = User(2, "Bob Sample", "bob@example.com", "+380671112233", "pbkdf2_sha256$00$synthetic-hash-2", None)
ADMIN = User(3, "Admin Demo", "admin@example.com", "+380931234500", "pbkdf2_sha256$00$x", None, is_admin=True)


@pytest.fixture
def privacy_env(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.INFO)
    stores = {
        "users": UserStorage(tmp_path / "users.json"),
        "tasks": TaskStorage(tmp_path / "tasks.json"),
        "consents": ConsentStorage(tmp_path / "consents.json"),
    }
    stores["users"].save([ALICE, BOB, ADMIN])
    stores["tasks"].save([
        Task(1, "Alice task A", owner_id=1),
        Task(2, "Alice task B", owner_id=1),
        Task(3, "Bob task", owner_id=2),
    ])
    stores["consents"].save([
        Consent(1, "OPTIONAL_ANALYTICS", True, "2026-09", "2026-09-01T10:00:00+00:00", None, "settings_page",
                history=[{"action": "grant", "at": "2026-09-01T10:00:00+00:00", "policy_version": "2026-09",
                          "source": "settings_page"}]),
        Consent(2, "MARKETING_EMAIL", True, "2026-09", "2026-09-02T10:00:00+00:00", None, "signup_form"),
    ])
    monkeypatch.setattr(api, "user_storage", stores["users"])
    monkeypatch.setattr(api, "storage", stores["tasks"])
    monkeypatch.setattr(api, "consent_storage", stores["consents"])
    return TestClient(api.app), stores


def as_user(user_id: int) -> dict:
    return {"X-User-Id": str(user_id)}
