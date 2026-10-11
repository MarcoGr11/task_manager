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
