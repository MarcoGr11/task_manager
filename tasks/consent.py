"""Purpose-specific consent records with evidence and history (Lab 4)."""
from dataclasses import dataclass, field

from .user_storage import JsonStorage

PURPOSES = {"MARKETING_EMAIL", "OPTIONAL_ANALYTICS"}
# Current policy text version per purpose; a consent given for an older version is not valid.
POLICY_VERSIONS = {"MARKETING_EMAIL": "2026-09", "OPTIONAL_ANALYTICS": "2026-09"}


@dataclass
class Consent:
    user_id: int
    purpose: str  # e.g. "MARKETING_EMAIL", "OPTIONAL_ANALYTICS"
    is_granted: bool
    policy_version: str
    granted_at: str | None
    withdrawn_at: str | None
    source: str
    updated_at: str | None = None
    history: list[dict] = field(default_factory=list)  # [{"action", "at", "policy_version", "source"}]


class ConsentStorage(JsonStorage):
    model = Consent
