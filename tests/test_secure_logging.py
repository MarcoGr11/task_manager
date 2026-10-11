"""Lab 4 Task 1: no original PII or secret may reach the log output (synthetic values only)."""
import json
import logging

import pytest
from fastapi.testclient import TestClient

from tasks import api
from tasks.logging_utils import install_sensitive_data_filter
from tasks.user_storage import UserStorage

EMAIL = "test.person@example.com"
PHONE = "+380501234567"
PASSWORD = "Synthetic-Pass-42"  # gitleaks:allow (synthetic test value)
TOKEN = "synthetic-token-abc123"
SENSITIVE = [EMAIL, PHONE, PASSWORD, TOKEN, "501234567"]

log = logging.getLogger("tasks.test")


@pytest.fixture(autouse=True)
def sanitizer(caplog):
    install_sensitive_data_filter()
    caplog.set_level(logging.INFO)


def assert_clean(text):
    for value in SENSITIVE:
        assert value not in text, f"leaked: {value}"


def test_text_json_and_exception_logs_are_sanitized(caplog):
    log.info(f"User {EMAIL} logged in from {PHONE}, password={PASSWORD}")
    log.info(json.dumps({"event": "login", "email": EMAIL, "phone": PHONE, "password": PASSWORD,
                         "access_token": TOKEN, "correlation_id": "corr-1"}))
    log.info("payload %s", {"refresh_token": TOKEN, "api_key": TOKEN, "secret": TOKEN})
    try:
        raise ValueError(f"Invalid email {EMAIL}")
    except ValueError:
        log.exception("Validation failed")

    assert_clean(caplog.text)
    assert "t***@example.com" in caplog.text
    assert "+**********67" in caplog.text
    assert '"password": "[REDACTED]"' in caplog.text and '"access_token": "[REDACTED]"' in caplog.text
    # diagnostic data is preserved and the JSON line is still valid JSON
    json_line = json.loads(caplog.records[1].getMessage())
    assert json_line["correlation_id"] == "corr-1" and json_line["event"] == "login"


def test_nested_object_in_exception_is_sanitized(caplog):
    nested = {"user": {"email": EMAIL, "profile": {"phone": PHONE}, "credentials": {"password": PASSWORD}}}
    try:
        raise RuntimeError(nested)
    except RuntimeError:
        log.exception("Import of %s failed", nested)

    assert_clean(caplog.text)
    assert caplog.records[0].exc_text.endswith(
        "RuntimeError: {'user': {'email': 't***@example.com', 'profile': {'phone': '+**********67'}, "
        "'credentials': {'password': '[REDACTED]'}}}"
    )


def test_registration_endpoint_logs_no_pii(caplog, monkeypatch, tmp_path):
    monkeypatch.setattr(api, "user_storage", UserStorage(tmp_path / "users.json"))
    client = TestClient(api.app)
    body = {"name": "Test Person", "email": EMAIL, "phone": PHONE, "password": PASSWORD}

    assert client.post("/api/users", json=body).status_code == 201
    assert client.post("/api/users", json=body).status_code == 422  # duplicate -> exception with email

    assert_clean(caplog.text)
    assert "Registration failed" in caplog.text and "t***@example.com" in caplog.text
