"""Consent Policy Gate and GRANT/REVOKE commands (Lab 4, Task 4).

The gate is called right before an optional, consent-based action (marketing e-mail,
optional analytics). Contract-based features (tasks CRUD, export, erasure) never call it.
"""
from collections.abc import Sequence
from dataclasses import dataclass, replace

from .consent import POLICY_VERSIONS, Consent
from .privacy import now_iso


def check_consent(user_id: int, purpose: str, consents: list[Consent]) -> bool:
    """ALLOW only for a granted consent for exactly this purpose and the current policy version.

    Consents are passed in freshly loaded on every call (no cache), so a REVOKE applies immediately.
    """
    return any(
        c.user_id == user_id and c.purpose == purpose and c.is_granted
        and c.policy_version == POLICY_VERSIONS[purpose]
        for c in consents
    )


def _find(consents: Sequence[Consent], user_id: int, purpose: str) -> Consent | None:
    return next((c for c in consents if c.user_id == user_id and c.purpose == purpose), None)


@dataclass(frozen=True)
class ConsentEvidence:
    """Value Object: who agreed to which policy version for which purpose, through which channel, when."""

    user_id: int
    purpose: str
    source: str
    at: str
    policy_version: str

    @classmethod
    def now(cls, user_id: int, purpose: str, source: str) -> "ConsentEvidence":
        return cls(user_id, purpose, source, now_iso(), POLICY_VERSIONS[purpose])

    def granted(self, previous: Consent | None) -> Consent:
        """A NEW granted record built from `previous` (never modified); `previous` itself if it is already valid."""
        if previous and previous.is_granted and previous.policy_version == self.policy_version:
            return previous
        base = previous or Consent(self.user_id, self.purpose, False, self.policy_version, None, None, self.source)
        entry = {"action": "grant", "at": self.at, "policy_version": self.policy_version, "source": self.source}
        return replace(base, is_granted=True, policy_version=self.policy_version, source=self.source,
                       granted_at=self.at, withdrawn_at=None, updated_at=self.at, history=[*base.history, entry])


def _upsert(consents: Sequence[Consent], record: Consent) -> tuple[Consent, ...]:
    """A new tuple where `record` replaces the entry for the same user and purpose (or is appended)."""
    return (*(c for c in consents if (c.user_id, c.purpose) != (record.user_id, record.purpose)), record)


def grant(consents: Sequence[Consent], user_id: int, purpose: str,
          source: str) -> tuple[tuple[Consent, ...], Consent, bool]:
    """Idempotent and side-effect free: the inputs are never modified. Returns (consents, record, changed)."""
    evidence = ConsentEvidence.now(user_id, purpose, source)
    previous = _find(consents, user_id, purpose)
    record = evidence.granted(previous)
    return _upsert(consents, record), record, record is not previous


def revoke(consents: list[Consent], user_id: int, purpose: str, source: str) -> tuple[list[Consent], Consent | None, bool]:
    """Idempotent: revoking a missing or already withdrawn consent changes nothing."""
    consent = _find(consents, user_id, purpose)
    if consent is None or not consent.is_granted:
        return consents, consent, False
    at = now_iso()
    consent.is_granted, consent.withdrawn_at, consent.updated_at = False, at, at
    consent.history.append({"action": "revoke", "at": at, "policy_version": consent.policy_version, "source": source})
    return consents, consent, True
