"""Lab 7 Task 2: grant() must not rewrite the caller's records - they are consent evidence."""
from tasks.consent import POLICY_VERSIONS, Consent
from tasks.consent_policy import grant

OLD_AT = "2025-01-05T10:00:00+00:00"
CURRENT = POLICY_VERSIONS["MARKETING_EMAIL"]


def test_regrant_for_new_policy_version_keeps_previous_evidence():
    old = Consent(1, "MARKETING_EMAIL", True, "2025-01", OLD_AT, None, "signup_form", OLD_AT,
                  [{"action": "grant", "at": OLD_AT, "policy_version": "2025-01", "source": "signup_form"}])
    consents = [old]

    new_consents, record, changed = grant(consents, 1, "MARKETING_EMAIL", "settings_page")

    # the new state: one valid grant for the current policy version, history continues
    assert changed and record.is_granted
    assert (record.policy_version, record.source) == (CURRENT, "settings_page")
    assert [h["policy_version"] for h in record.history] == ["2025-01", CURRENT]
    assert list(new_consents) == [record]
    # the evidence the caller holds (what was accepted in 2025, when and how) is not rewritten
    assert (old.policy_version, old.granted_at, old.source) == ("2025-01", OLD_AT, "signup_form")
    assert len(old.history) == 1
    assert consents == [old]


def test_first_grant_does_not_touch_callers_list():
    consents = []
    new_consents, record, changed = grant(consents, 1, "MARKETING_EMAIL", "api")
    assert changed and list(new_consents) == [record]
    assert consents == []
