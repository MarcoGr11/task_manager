"""PA-1 (PM-001): the operational readiness gate catches an alert without a runbook and an SLI without an alert."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ops_audit", Path(__file__).parents[1] / "scripts" / "ops_audit.py")
ops_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops_audit)


def test_repository_passes_ops_audit():
    assert ops_audit.audit() == []


def test_missing_runbook_and_unalerted_sli_are_reported(tmp_path):
    (tmp_path / "monitoring").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/rb.md").write_text('<a id="t1"></a>')
    (tmp_path / "monitoring/alerts.yml").write_text("""groups:
  - name: g
    rules:
      - {alert: Ok, labels: {severity: SEV1, role: SRE}, annotations: {runbook_url: docs/rb.md#t1}}
      - {alert: NoPage, labels: {severity: SEV2, role: SRE}, annotations: {runbook_url: docs/none.md}}
""")
    (tmp_path / "docs/slo.yaml").write_text("slis:\n  - {id: a, alert: Ok, slo: 99, sla: 98}\n"
                                            "  - {id: b, slo: 99, sla: 99.5}\n")

    problems = ops_audit.audit(tmp_path)

    assert len(problems) == 3
    assert "NoPage" in problems[0] and "SLI b: alert" in problems[1] and "SLA 99.5" in problems[2]
