import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("backup", Path(__file__).parents[1] / "scripts" / "backup.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


def stores(tmp_path, monkeypatch, tasks):
    for name, env in [("tasks", "TASKS_DB"), ("users", "USERS_DB"), ("consents", "CONSENTS_DB")]:
        monkeypatch.setenv(env, str(tmp_path / f"{name}.json"))
    (tmp_path / "tasks.json").write_text(json.dumps(tasks))
    (tmp_path / "users.json").write_text(json.dumps([{"id": 1}]))
    (tmp_path / "consents.json").write_text("[]")


def test_full_plus_incremental_restore_after_corruption(tmp_path, monkeypatch):
    monkeypatch.delenv("BACKUP_PASSPHRASE", raising=False)
    stores(tmp_path, monkeypatch, [{"id": 1}])
    full = backup.backup(tmp_path / "b", incremental=False)
    (tmp_path / "tasks.json").write_text(json.dumps([{"id": 1}, {"id": 2}]))
    incr = backup.backup(tmp_path / "b", incremental=True)
    assert backup.read_archive(incr)[0]["included"] == ["tasks"]
    (tmp_path / "tasks.json").write_text("{corrupt")
    assert backup.main(["restore", str(full), str(incr)]) == 0
    assert len(json.loads((tmp_path / "tasks.json").read_text())) == 2


def test_restore_refuses_incomplete_chain(tmp_path, monkeypatch):
    monkeypatch.delenv("BACKUP_PASSPHRASE", raising=False)
    stores(tmp_path, monkeypatch, [{"id": 1}])
    backup.backup(tmp_path / "b", incremental=False)
    (tmp_path / "tasks.json").write_text(json.dumps([{"id": 1}, {"id": 2}]))
    incr = backup.backup(tmp_path / "b", incremental=True)
    (tmp_path / "tasks.json").write_text("{corrupt")
    assert backup.main(["restore", str(incr)]) == 1  # base full archive missing
    assert (tmp_path / "tasks.json").read_text() == "{corrupt"  # nothing written


def test_encrypted_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKUP_PASSPHRASE", "test-only-passphrase")
    stores(tmp_path, monkeypatch, [{"id": 7}])
    archive = backup.backup(tmp_path / "b", incremental=False)
    assert archive.name.endswith(".tar.gz.enc")
    assert b"manifest" not in archive.read_bytes()  # ciphertext, not a plain tar
    assert backup.main(["verify", str(archive)]) == 0
