"""Lab 4 Task 2: Right of Access export - completeness, minimization, authorization."""
from conftest import ALICE, as_user


def test_own_export_contains_all_sections_and_only_own_records(privacy_env, caplog):
    client, _ = privacy_env
    response = client.get("/api/users/1/personal-data", headers=as_user(1))

    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"export_metadata", "profile", "settings", "activity", "consents"}
    assert data["export_metadata"]["subject_id"] == 1
    assert data["export_metadata"]["schema_version"] == "1.0"
    assert data["export_metadata"]["generated_at"].endswith("+00:00")  # explicit UTC
    assert data["profile"] == {"name": ALICE.name, "email": ALICE.email, "phone": ALICE.phone}
    assert data["settings"] == {"marketing_opt_in_source": "signup_form"}
    assert [t["title"] for t in data["activity"]["tasks"]] == ["Alice task A", "Alice task B"]
    assert [c["purpose"] for c in data["consents"]] == ["OPTIONAL_ANALYTICS"]  # Bob's consent not mixed in
    # the export itself is not logged: only the fact, with masked/absent PII
    assert ALICE.email not in caplog.text and ALICE.phone not in caplog.text
    assert "personal_data_export result=success actor_id=1 subject_id=1" in caplog.text


def test_export_excludes_security_sensitive_fields(privacy_env):
    client, _ = privacy_env
    text = client.get("/api/users/1/personal-data", headers=as_user(1)).text

    for forbidden in ["password_hash", "reset_token", "is_admin", "anonymized_at"]:
        assert f'"{forbidden}":' not in text  # never present as a key
    for secret in [ALICE.password_hash, ALICE.reset_token]:
        assert secret not in text


def test_foreign_and_missing_ids_get_identical_denial(privacy_env, caplog):
    client, _ = privacy_env
    foreign = client.get("/api/users/2/personal-data", headers=as_user(1))
    missing = client.get("/api/users/999/personal-data", headers=as_user(1))

    assert foreign.status_code == missing.status_code == 403
    assert foreign.json() == missing.json() == {"detail": "Forbidden"}  # no hint whether id 2 exists
    assert "bob" not in foreign.text.lower() and "bob@example.com" not in caplog.text


def test_admin_cannot_export_others_and_auth_is_required(privacy_env):
    client, _ = privacy_env
    assert client.get("/api/users/1/personal-data", headers=as_user(3)).status_code == 403
    assert client.get("/api/users/1/personal-data").status_code == 401
