"""Backup, verify and restore the JSON data stores (runbook docs/runbooks/RB-001.md).

Usage (from the repository root, same environment as the API):
    python scripts/backup.py backup --dest backups [--incremental]
    python scripts/backup.py verify backups/<archive>
    python scripts/backup.py restore backups/<full> [backups/<incr> ...]

Stores come from TASKS_DB, USERS_DB, CONSENTS_DB (defaults as in tasks/api.py).
A full archive holds every store, an incremental one only stores whose SHA-256 changed
since the previous backup in --dest. Every manifest lists the hashes of ALL stores, so
restoring "full + incrementals in order" is checked against the last manifest.
If BACKUP_PASSPHRASE is set, archives are encrypted with `openssl enc -aes-256-cbc -pbkdf2`.
Exit code: 0 ok, 1 verification/restore failure.
"""
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

STORES = {"tasks": ("TASKS_DB", "tasks.json"), "users": ("USERS_DB", "users.json"),
          "consents": ("CONSENTS_DB", "consents.json")}
STATE = "last_manifest.json"
OPENSSL = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-pass", "env:BACKUP_PASSPHRASE"]


def store_paths() -> dict[str, Path]:
    return {name: Path(os.getenv(env, default)) for name, (env, default) in STORES.items()}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def records(data: bytes) -> int:
    return len(json.loads(data)) if data.strip() else 0


def snapshot() -> dict[str, bytes]:
    return {name: path.read_bytes() for name, path in store_paths().items() if path.exists()}


def _crypt(blob: bytes, decrypt: bool) -> bytes:
    if not os.getenv("BACKUP_PASSPHRASE"):
        return blob
    cmd = OPENSSL + (["-d"] if decrypt else [])
    return subprocess.run(cmd, input=blob, capture_output=True, check=True).stdout


def _previous(dest: Path, incremental: bool) -> dict | None:
    state = dest / STATE
    return json.loads(state.read_text()) if incremental and state.exists() else None


def _tar(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, blob in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(blob)
            tar.addfile(info, io.BytesIO(blob))
    return buf.getvalue()


def backup(dest: Path, incremental: bool) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    data = snapshot()
    files = {n: {"sha256": sha256(b), "records": records(b)} for n, b in data.items()}
    previous = _previous(dest, incremental)
    old = previous["files"] if previous else {}
    changed = {n: b for n, b in data.items() if old.get(n, {}).get("sha256") != files[n]["sha256"]}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    kind = "incr" if previous else "full"
    manifest = {"created_at": stamp, "kind": kind, "included": sorted(changed), "files": files}
    blob = _tar({"manifest.json": json.dumps(manifest, indent=2).encode(), **changed})
    suffix = ".tar.gz.enc" if os.getenv("BACKUP_PASSPHRASE") else ".tar.gz"
    archive = dest / f"{stamp}-{kind}{suffix}"
    archive.write_bytes(_crypt(blob, decrypt=False))
    (dest / STATE).write_text(json.dumps(manifest, indent=2))
    print(f"{kind} backup {archive} included={manifest['included']} "
          + " ".join(f"{n}={f['records']}" for n, f in manifest["files"].items()))
    return archive


def read_archive(archive: Path) -> tuple[dict, dict[str, bytes]]:
    blob = _crypt(archive.read_bytes(), decrypt=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        members = {m.name: tar.extractfile(m).read() for m in tar.getmembers()}
    manifest = json.loads(members.pop("manifest.json"))
    return manifest, members


def verify(archive: Path) -> bool:
    manifest, members = read_archive(archive)
    bad = [n for n, blob in members.items() if sha256(blob) != manifest["files"][n]["sha256"]]
    print(f"verify {archive.name}: kind={manifest['kind']} files={sorted(members)} "
          f"{'FAIL ' + str(bad) if bad else 'OK'}")
    return not bad


def restore(archives: list[Path]) -> bool:
    state: dict[str, bytes] = {}
    manifest = {}
    for archive in archives:
        manifest, members = read_archive(archive)
        state.update(members)
    expected = manifest["files"]
    bad = [n for n in expected if n not in state or sha256(state[n]) != expected[n]["sha256"]]
    if bad:
        print(f"restore ABORTED: hash mismatch or missing {bad}, nothing written")
        return False
    for name, path in store_paths().items():
        if name in state:
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(state[name])
            os.replace(tmp, path)  # atomic per file, same as save_all in tasks/user_storage.py
    print("restored " + " ".join(f"{n}={expected[n]['records']}" for n in sorted(expected))
          + f" from {[a.name for a in archives]}")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--dest", type=Path, default=Path("backups"))
    b.add_argument("--incremental", action="store_true")
    sub.add_parser("verify").add_argument("archive", type=Path)
    sub.add_parser("restore").add_argument("archives", type=Path, nargs="+")
    args = parser.parse_args(argv)
    if args.cmd == "backup":
        backup(args.dest, args.incremental)
        return 0
    ok = verify(args.archive) if args.cmd == "verify" else restore(args.archives)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
