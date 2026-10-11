"""Consent Policy Gate and GRANT/REVOKE commands (Lab 4, Task 4).

The gate is called right before an optional, consent-based action (marketing e-mail,
optional analytics). Contract-based features (tasks CRUD, export, erasure) never call it.
"""
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


def _find(consents: list[Consent], user_id: int, purpose: str) -> Consent | None:
    return next((c for c in consents if c.user_id == user_id and c.purpose == purpose), None)


def grant(consents: list[Consent], user_id: int, purpose: str, source: str) -> tuple[Consent, bool]:
    """Idempotent: an existing valid grant is left untouched. Returns (record, changed)."""
    version = POLICY_VERSIONS[purpose]
    consent = _find(consents, user_id, purpose)
    if consent and consent.is_granted and consent.policy_version == version:
        return consent, False
    at = now_iso()
    if consent is None:
        consent = Consent(user_id, purpose, False, version, None, None, source)
        consents.append(consent)
    consent.is_granted, consent.policy_version, consent.source = True, version, source
    consent.granted_at, consent.withdrawn_at, consent.updated_at = at, None, at
    consent.history.append({"action": "grant", "at": at, "policy_version": version, "source": source})
    return consent, True


def revoke(consents: list[Consent], user_id: int, purpose: str, source: str) -> tuple[Consent | None, bool]:
    """Idempotent: revoking a missing or already withdrawn consent changes nothing."""
    consent = _find(consents, user_id, purpose)
    if consent is None or not consent.is_granted:
        return consent, False
    at = now_iso()
    consent.is_granted, consent.withdrawn_at, consent.updated_at = False, at, at
    consent.history.append({"action": "revoke", "at": at, "policy_version": consent.policy_version, "source": source})
    return consent, True
