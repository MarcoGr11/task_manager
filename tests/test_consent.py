"""Lab 4 Task 4: consent engine - GRANT -> ALLOW -> REVOKE -> DENY, purpose isolation, evidence."""
from unittest.mock import Mock

from conftest import as_user
from tasks import api
from tasks.consent import Consent
from tasks.consent_policy import check_consent

SEND = "/api/users/1/send-marketing-email"
GRANT = "/api/users/1/consents/MARKETING_EMAIL/grant?source=settings_page"
REVOKE = "/api/users/1/consents/MARKETING_EMAIL/revoke?source=settings_page"


def test_grant_allow_revoke_deny_scenario(privacy_env, monkeypatch):
    client, stores = privacy_env
    sender = Mock()
    monkeypatch.setattr(api, "send_marketing_email", sender)
    alice = as_user(1)

    # initial state: Alice only consented to OPTIONAL_ANALYTICS -> marketing is denied, nothing sent
    assert client.post(SEND, headers=alice).status_code == 403
    assert sender.call_count == 0

    # GRANT (twice: idempotent, one record, one history entry)
    assert client.post(GRANT, headers=alice).json()["is_granted"] is True
    client.post(GRANT, headers=alice)
    response = client.post(SEND, headers=alice)
    assert response.status_code == 200 and response.json()["decision"] == "ALLOW"
    assert sender.call_count == 1

    # REVOKE (twice: idempotent) -> applies immediately, no side effect
    client.post(REVOKE, headers=alice)
    client.post(REVOKE, headers=alice)
    assert client.post(SEND, headers=alice).status_code == 403
    assert sender.call_count == 1

    # evidence: single record with policy version, timestamps, source and full history
    records = [c for c in stores["consents"].load() if c.user_id == 1 and c.purpose == "MARKETING_EMAIL"]
    assert len(records) == 1
    record = records[0]
    assert record.policy_version == "2026-09" and record.source == "settings_page"
    assert record.granted_at and record.withdrawn_at and record.updated_at
    assert [h["action"] for h in record.history] == ["grant", "revoke"]


def test_consent_is_purpose_specific_and_version_bound():
    consents = [
        Consent(1, "MARKETING_EMAIL", True, "2026-09", "2026-09-01T00:00:00+00:00", None, "api"),
        Consent(2, "MARKETING_EMAIL", True, "2025-01", "2025-01-01T00:00:00+00:00", None, "api"),
    ]
    assert check_consent(1, "MARKETING_EMAIL", consents)
    assert not check_consent(1, "OPTIONAL_ANALYTICS", consents)  # no spill-over to another purpose
    assert not check_consent(2, "MARKETING_EMAIL", consents)  # outdated policy version
    assert not check_consent(3, "MARKETING_EMAIL", consents)  # no record at all


def test_consent_commands_are_authorized_and_validated(privacy_env):
    client, _ = privacy_env
    assert client.post(GRANT, headers=as_user(2)).status_code == 403  # Bob cannot grant for Alice
    assert client.post("/api/users/1/consents/SELL_DATA/grant", headers=as_user(1)).status_code == 422
    # contract features are not gated by marketing consent
    assert client.get("/api/users/1/personal-data", headers=as_user(1)).status_code == 200
