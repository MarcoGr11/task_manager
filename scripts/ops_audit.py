"""Operational readiness gate (Lab 12, PA-1 from docs/incidents/pm-001.md).

INC-001 happened because a dependency shipped with no SLI metric, no alert and no runbook.
This check fails CI when the ops docs drift apart again:
  1. every alert in monitoring/alerts.yml has severity, role and a runbook_url whose file and anchor exist;
  2. every SLI in docs/slo.yaml names an existing alert, and its SLA is looser than its SLO.
Usage: python scripts/ops_audit.py   (exit 1 and one line per problem)
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def alert_problems(alerts: dict, root: Path = ROOT) -> list[str]:
    problems = []
    for name, rule in alerts.items():
        labels, url = rule.get("labels", {}), rule.get("annotations", {}).get("runbook_url", "")
        if not {"severity", "role"} <= labels.keys():
            problems.append(f"alert {name}: severity/role label missing")
        path, _, anchor = url.partition("#")
        page = root / path
        if not url or not page.is_file():
            problems.append(f"alert {name}: runbook_url '{url}' does not exist")
        elif anchor and f'id="{anchor}"' not in page.read_text(encoding="utf-8"):
            problems.append(f"alert {name}: anchor #{anchor} not found in {path}")
    return problems


def sli_problems(slis: list[dict], alerts: dict) -> list[str]:
    problems = []
    for sli in slis:
        if sli.get("alert") not in alerts:
            problems.append(f"SLI {sli['id']}: alert '{sli.get('alert')}' not in monitoring/alerts.yml")
        if not sli["sla"] < sli["slo"]:
            problems.append(f"SLI {sli['id']}: SLA {sli['sla']} must be looser than SLO {sli['slo']}")
    return problems


def audit(root: Path = ROOT) -> list[str]:
    rules = yaml.safe_load((root / "monitoring/alerts.yml").read_text(encoding="utf-8"))
    alerts = {r["alert"]: r for group in rules["groups"] for r in group["rules"]}
    slis = yaml.safe_load((root / "docs/slo.yaml").read_text(encoding="utf-8"))["slis"]
    return alert_problems(alerts, root) + sli_problems(slis, alerts)


if __name__ == "__main__":
    found = audit()
    print("\n".join(found) or "ops audit: OK")
    sys.exit(1 if found else 0)
