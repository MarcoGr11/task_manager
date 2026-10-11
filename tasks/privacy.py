"""Personal data export (GDPR Art. 15) built from all stores that hold user data."""
from dataclasses import asdict
from datetime import UTC, datetime

from .consent import Consent
from .models import Task
from .user import User

EXPORT_SCHEMA_VERSION = "1.0"
# Data minimization: these User fields are NEVER exported.
#   password_hash - credential material
#   reset_token   - live account-recovery secret
#   is_admin      - internal security/authorization flag
#   anonymized_at - internal erasure bookkeeping
EXCLUDED_USER_FIELDS = ["password_hash", "reset_token", "is_admin", "anonymized_at"]
PROFILE_FIELDS = ["name", "email", "phone"]


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def build_export(user: User, tasks: list[Task], consents: list[Consent]) -> dict:
    """Whitelist-based: only fields named here leave the system; new User fields stay private."""
    return {
        "export_metadata": {
            "generated_at": now_iso(),
            "schema_version": EXPORT_SCHEMA_VERSION,
            "subject_id": user.id,
            "categories": ["profile", "settings", "activity", "consents"],
            "excluded_fields": EXCLUDED_USER_FIELDS,
        },
        "profile": {f: getattr(user, f) for f in PROFILE_FIELDS},  # source: users.json
        "settings": {"marketing_opt_in_source": user.marketing_opt_in_source},  # source: users.json
        "activity": {  # source: tasks.json, only tasks owned by the subject
            "tasks": [t.to_dict() for t in tasks if t.owner_id == user.id],
        },
        "consents": [asdict(c) for c in consents if c.user_id == user.id],  # source: consents.json
    }


# Erasure policy (GDPR Art. 17), applied by anonymize_user():
#   User.name / email / phone          ANONYMIZE  -> "Deleted User" / deleted-user-{id}@anon.local / ""
#                                                   (id keeps the email unique; nothing derived from the old value)
#   User.password_hash / reset_token   DELETE     -> None
#   User.marketing_opt_in_source       RETAIN     (channel name, does not identify a person)
#   Task (title, status, owner_id)     RETAIN     business records; owner_id now points at an anonymous
#                                                 profile, so the link no longer identifies anyone
#   Consent records                    ANONYMIZE  purpose / policy_version / timestamps / history kept as
#                                                 audit evidence; a granted consent is withdrawn
#   Application logs                   SKIP       never contained raw PII (SensitiveDataFilter)
ANONYMOUS_NAME = "Deleted User"


def anonymous_email(user_id: int) -> str:
    return f"deleted-user-{user_id}@anon.local"


def _anonymize_consent(consent: Consent, at: str) -> None:
    if consent.is_granted:
        consent.is_granted = False
        consent.withdrawn_at = at
        consent.history.append({"action": "withdrawn_by_erasure", "at": at,
                                "policy_version": consent.policy_version, "source": "erasure_request"})
    consent.updated_at = at


def anonymize_user(user: User, consents: list[Consent], at: str) -> bool:
    """Mutate the in-memory records only; the caller persists them all at once.

    Returns False (and changes nothing) if the user is already anonymized: idempotent.
    """
    if user.anonymized_at is not None:
        return False
    user.name = ANONYMOUS_NAME
    user.email = anonymous_email(user.id)
    user.phone = ""
    user.password_hash = None
    user.reset_token = None
    user.anonymized_at = at
    for consent in consents:
        if consent.user_id == user.id:
            _anonymize_consent(consent, at)
    return True
