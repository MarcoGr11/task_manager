"""Lab 4 Task 3: anonymization workflow - PII gone everywhere, records kept, idempotent, atomic, authorized."""
import pytest

from conftest import ALICE, as_user
from tasks import privacy


def snapshot(stores):
    return {name: s.path.read_text() for name, s in stores.items()}


def test_anonymize_removes_pii_keeps_records_and_is_idempotent(privacy_env, caplog):
    client, stores = privacy_env

    response = client.post("/api/users/1/anonymize", headers=as_user(1))

    assert response.status_code == 200
    first = response.json()
    assert first["status"] == "anonymized"
    after = snapshot(stores)
    for original in [ALICE.name, ALICE.email, ALICE.phone, ALICE.password_hash, ALICE.reset_token]:
        assert original not in after["users"] and original not in after["consents"]
        assert original not in caplog.text
    alice = stores["users"].find(stores["users"].load(), 1)
    assert (alice.name, alice.email, alice.phone) == ("Deleted User", "deleted-user-1@anon.local", "")
    assert alice.password_hash is None and alice.reset_token is None
    # business records retained and still pointing at an existing (anonymous) user
    tasks = stores["tasks"].load()
    assert [t.owner_id for t in tasks] == [1, 1, 2]
    user_ids = {u.id for u in stores["users"].load()}
    assert all(t.owner_id in user_ids for t in tasks)
    # consent evidence kept, but withdrawn
    consent = next(c for c in stores["consents"].load() if c.user_id == 1)
    assert consent.purpose == "OPTIONAL_ANALYTICS" and consent.granted_at and not consent.is_granted
    assert consent.history[-1]["action"] == "withdrawn_by_erasure"
    # other users untouched
    assert "bob@example.com" in after["users"]
    # privacy-safe audit event
    assert '"event": "user_anonymized"' in caplog.text and '"result": "success"' in caplog.text

    # repeat: same answer, no state change, no PII restored
    again = client.post("/api/users/1/anonymize", headers=as_user(1))
    assert again.status_code == 200 and again.json() == first
    assert snapshot(stores) == after
    assert '"result": "already_anonymized"' in caplog.text
    # reporting over retained records still works
    assert client.get("/api/users/1/personal-data", headers=as_user(1)).json()["activity"]["tasks"]


def test_failure_mid_way_writes_nothing(privacy_env, monkeypatch):
    client, stores = privacy_env
    before = snapshot(stores)

    def boom(*_):
        raise RuntimeError("disk full")

    monkeypatch.setattr(privacy, "_anonymize_consent", boom)  # fails after User was changed in memory
    response = client.post("/api/users/1/anonymize", headers=as_user(1))

    assert response.status_code == 500
    assert snapshot(stores) == before


@pytest.mark.parametrize("actor, expected", [(2, 403), (3, 200)])  # foreign user denied, admin allowed
def test_only_owner_or_admin_may_anonymize(privacy_env, actor, expected):
    client, stores = privacy_env
    before = snapshot(stores)["users"]

    assert client.post("/api/users/1/anonymize", headers=as_user(actor)).status_code == expected
    assert (snapshot(stores)["users"] == before) == (expected == 403)
    assert client.get("/api/users/1/anonymize", headers=as_user(1)).status_code == 405  # not via GET
