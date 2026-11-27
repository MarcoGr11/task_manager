#!/usr/bin/env python3
"""Documentation decay audit from real git commands.

Prints every command before its output, so the report doubles as a command log.
Exit code 1 when a living document has drifted from code (missing route or env var,
or more than DRIFT code commits since its last update), 0 otherwise.

Usage: python scripts/doc_audit.py > docs/audit/decay_metrics.txt
"""
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CODE_DIR = "tasks"
SUSPICIOUS, STALE, DRIFT = 90, 180, 20
CARRIERS = [
    "README.md", "docs/api/openapi.yaml", "docs/architecture/sdd.md", "docs/architecture/isd.md",
    "docs/developer/maintenance.md", "docs/developer/handover.md", "docs/developer/CONTRIBUTING.md",
    "docs/architecture/adr/0001-json-file-storage.md", "docs/architecture/adr/0002-notifier-retry-fallback.md",
    "docs/architecture/adr/0003-openapi-as-source-of-truth.md", "docs/architecture/adr/0004-docs-as-code-mkdocs.md",
    "mkdocs.yml", ".github/workflows/docs.yml",
    "FINANCIAL_LEDGER.md", ".github/workflows/complexity.yml", ".githooks/pre-commit", ".githooks/complexity_check.sh",
    "docker-compose.monitoring.yml", "docker-compose.sonar.yml", "monitoring/prometheus.yml",
    "sonar-project.properties", "pytest.ini", ".env.example", ".gitleaks.toml", "requirements.txt",
]
# Documents that describe the tasks/ code and therefore must follow it.
LIVING = {"docs/api/openapi.yaml", "docs/architecture/sdd.md", "docs/architecture/isd.md"}
ROUTE = re.compile(r'@app\.(get|post|put|patch|delete)\("([^"]+)"')
ENV = re.compile(r'getenv\("([A-Z_]+)"')


def sh(cmd: str, show: bool = True) -> str:
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
    if show:
        print(f"$ {cmd}\n{out}")
    return out


def classify(age: int) -> str:
    if age > STALE:
        return "stale (>180)"
    return "suspicious (>90)" if age > SUSPICIOUS else "ok"


def carrier_row(path: str, today: date) -> tuple[str, bool]:
    last = sh(f"git log -1 --format=%cs -- {path}", show=False)
    if not last:
        total = sh(f"git log --oneline -- {CODE_DIR} | wc -l", show=False)
        return f"{path:<55} {'-':<10} {'-':>5}  {'відсутній у git':<16} {total:>4}", path in LIVING
    age = (today - date.fromisoformat(last)).days
    sha = sh(f"git log -1 --format=%h -- {path}", show=False)
    behind = int(sh(f"git log --oneline {sha}..HEAD -- {CODE_DIR} | wc -l", show=False))
    drift = path in LIVING and behind > DRIFT
    return f"{path:<55} {last:<10} {age:>5}  {classify(age):<16} {behind:>4}{'  DRIFT' if drift else ''}", drift


def carriers(today: date) -> bool:
    print(f"\n## 1. Вік носіїв (сьогодні {today}; >{SUSPICIOUS} підозрілий, >{STALE} застарілий)")
    print("Команди на кожен файл: git log -1 --format=%cs -- <file>; git log --oneline <last>..HEAD -- tasks | wc -l")
    print(f"{'файл':<55} {'остання':<10} {'днів':>5}  {'стан':<16} {'код після':>4}")
    failed = False
    for path in CARRIERS:
        row, drift = carrier_row(path, today)
        print(row)
        failed |= drift
    return failed


def ratio() -> None:
    print("\n## 2. Code-Doc Change Ratio")
    code = int(sh(f"git log --oneline -- {CODE_DIR} | wc -l"))
    docs = int(sh("git log --oneline -- '*.md' docs | wc -l"))
    print(f"Ratio code:doc = {code}:{docs}" + (f" = {code / docs:.1f}" if docs else " (документація не змінювалась)"))


def ghosts() -> None:
    print("\n## 3. Порожні коміти з 'docs' у повідомленні (документ обіцяно, файлів у дереві немає)")
    count = 0
    for line in sh("git log --format='%h %cs %s' -i --grep=docs", show=False).splitlines():
        if not sh(f"git diff-tree --no-commit-id -r --root --name-only {line.split()[0]}", show=False):
            print(line)
            count += 1
    print(f"Разом: {count}")


def dead_links() -> None:
    print("\n## 4. Посилання з коду на файли документації")
    for hit in sh("git grep -nE 'README[_A-Z0-9]*\\.md|docs/[a-z0-9/_-]+\\.md' -- tasks mock_notifier", show=False).splitlines():
        target = re.search(r"(README[_A-Z0-9]*\.md|docs/[a-z0-9/_-]+\.md)", hit)[1]
        found = Path(target).exists() or sh(f"git ls-files '*{target}'", show=False)
        print(f"{hit}\n  -> {target}: {'існує' if found else 'DEAD (немає в git і на диску)'}")


def coverage() -> bool:
    print("\n## 5. Покриття коду документацією (маршрути tasks/api.py -> openapi.yaml, змінні оточення tasks/ -> ISD)")
    code = "".join(p.read_text(encoding="utf-8") for p in Path(CODE_DIR).glob("*.py"))
    routes = ROUTE.findall(Path("tasks/api.py").read_text(encoding="utf-8"))
    checks = [(f"{m} {p}", f"\n  {p}:", ("docs/api/openapi.yaml",)) for m, p in routes]
    checks += [(f"env {v}", v, ("docs/architecture/isd.md",)) for v in sorted(set(ENV.findall(code)))]
    failed = False
    for label, needle, docs in checks:
        missing = [d for d in docs if not Path(d).exists() or needle not in Path(d).read_text(encoding="utf-8")]
        failed |= bool(missing)
        print(f"{label:<55} {'OK' if not missing else 'НЕМАЄ в ' + ', '.join(missing)}")
    return failed


def access() -> None:
    print("\n## 6. Access Evidence")
    out = sh("gh api repos/MarcoGr11/task_manager/traffic/popular/paths 2>/dev/null")
    if not out:
        print("gh недоступний: потребує підтвердження студента")
    views = re.findall(r'"path":"([^"]+\.md)"', out)
    print(f"Перегляди .md-файлів на GitHub за 14 днів: {', '.join(views) or 'не зафіксовано'}. "
          "Хто реально читає документацію: потребує підтвердження студента.")


def main() -> int:
    print(f"# Documentation decay audit, HEAD {sh('git rev-parse --short HEAD', show=False)}")
    drift = carriers(date.today())
    ratio()
    ghosts()
    dead_links()
    missing = coverage()
    access()
    verdict = "FAIL" if drift or missing else "PASS"
    print(f"\n## Вердикт: {verdict}")
    return 1 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
