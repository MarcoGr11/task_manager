import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("fin_sim", Path(__file__).parents[1] / "scripts" / "fin_sim.py")
fin_sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fin_sim)


def write_report(path: Path, ncloc="72621", sqale="10797") -> Path:
    measures = [{"metric": "ncloc", "value": ncloc}, {"metric": "sqale_index", "value": sqale}]
    path.write_text(json.dumps({"component": {"key": "demo_key", "measures": measures}}), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("HOURLY_RATE", "40")
    monkeypatch.delenv("OVERLOAD_COEFF", raising=False)
    monkeypatch.delenv("DISCOUNT_RATE", raising=False)


def test_principal_formula():
    assert fin_sim.principal(10797, 40, 1.3) == pytest.approx(9357.40)


def test_cost_of_delay_formula():
    assert fin_sim.cost_of_delay(72621, 40) == pytest.approx(29048.40)


def test_schedule_discounts_each_month_and_accumulates():
    rows = fin_sim.schedule(cod=1000, debt=1500, discount_rate=0.01, months=2)
    assert rows[0]["factor"] == pytest.approx(1 / 1.01)
    assert rows[0]["npv"] == pytest.approx(1000 / 1.01 - 1500)
    assert rows[1]["effect"] == pytest.approx(1000 / 1.01 ** 2)
    assert rows[1]["npv"] == pytest.approx(1000 / 1.01 + 1000 / 1.01 ** 2 - 1500)


def test_payback_is_first_positive_month():
    assert fin_sim.payback_month(fin_sim.schedule(1000, 1500, 0.01)) == 2


def test_npv_of_exactly_zero_is_not_payback():
    assert fin_sim.payback_month(fin_sim.schedule(1000, 1000, 0.0, months=1)) is None


def test_no_payback_within_six_months():
    assert fin_sim.payback_month(fin_sim.schedule(100, 10_000, 0.01)) is None


def test_ledger_pass(tmp_path):
    output = tmp_path / "ledger.md"
    assert fin_sim.main(["x", str(write_report(tmp_path / "r.json")), str(output)]) == 0
    text = output.read_text(encoding="utf-8")
    assert "demo_key" in text and "9357.40" in text and "29048.40" in text
    assert "Місяць окупності (Payback Period): 1" in text and "**PASS**" in text
    assert text.count("\n| ") - text.count("Параметр") >= 12


def test_ledger_fail_warns_and_returns_one(tmp_path):
    output = tmp_path / "ledger.md"
    assert fin_sim.main(["x", str(write_report(tmp_path / "r.json", ncloc="100", sqale="600000")), str(output)]) == 1
    text = output.read_text(encoding="utf-8")
    assert "**FAIL**" in text and "Попередження" in text


def test_missing_file(tmp_path, capsys):
    assert fin_sim.main(["x", str(tmp_path / "absent.json"), str(tmp_path / "o.md")]) == 2
    assert "файл не знайдено" in capsys.readouterr().err


def test_invalid_json(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert fin_sim.main(["x", str(bad), str(tmp_path / "o.md")]) == 2
    assert "некоректний JSON" in capsys.readouterr().err


def test_missing_metric(tmp_path, capsys):
    report = tmp_path / "r.json"
    report.write_text(json.dumps({"component": {"key": "k", "measures": [{"metric": "ncloc", "value": "1"}]}}), encoding="utf-8")
    assert fin_sim.main(["x", str(report), str(tmp_path / "o.md")]) == 2
    assert "sqale_index" in capsys.readouterr().err


def test_rate_outside_range_is_rejected(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOURLY_RATE", "51")
    assert fin_sim.main(["x", str(write_report(tmp_path / "r.json")), str(tmp_path / "o.md")]) == 2
    assert "35-50" in capsys.readouterr().err


def test_missing_rate(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("HOURLY_RATE")
    assert fin_sim.main(["x", str(write_report(tmp_path / "r.json")), str(tmp_path / "o.md")]) == 2
    assert "HOURLY_RATE" in capsys.readouterr().err
