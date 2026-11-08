#!/usr/bin/env python3
"""Financial simulator of technical debt: reads a SonarCloud measures JSON, writes FINANCIAL_LEDGER.md.

Usage: HOURLY_RATE=40 python scripts/fin_sim.py report.json [output.md]
Environment: HOURLY_RATE (35-50, required), OVERLOAD_COEFF (default 1.3), DISCOUNT_RATE (default 0.01).
"""
import json
import os
import sys
from pathlib import Path

MONTHS = 6
DEFAULT_LEDGER = Path(__file__).parents[1] / "FINANCIAL_LEDGER.md"


class SimError(Exception):
    pass


def principal(sqale_index: float, hourly_rate: float, overload_coeff: float) -> float:
    return sqale_index / 60 * hourly_rate * overload_coeff


def cost_of_delay(ncloc: float, hourly_rate: float) -> float:
    return ncloc / 100 * hourly_rate


def schedule(cod: float, debt: float, discount_rate: float, months: int = MONTHS) -> list[dict]:
    rows = []
    cumulative = 0.0
    for month in range(1, months + 1):
        factor = 1 / (1 + discount_rate) ** month
        effect = cod * factor
        cumulative += effect
        rows.append({"month": month, "factor": factor, "effect": effect, "npv": cumulative - debt})
    return rows


def payback_month(rows: list[dict]) -> int | None:
    return next((row["month"] for row in rows if row["npv"] > 0), None)


def load_report(path: Path) -> dict:
    try:
        component = json.loads(path.read_text(encoding="utf-8"))["component"]
        measures = {m["metric"]: m["value"] for m in component["measures"]}
        return {"key": component["key"], "ncloc": int(measures["ncloc"]), "sqale_index": int(measures["sqale_index"])}
    except FileNotFoundError:
        raise SimError(f"файл не знайдено: {path}") from None
    except json.JSONDecodeError as error:
        raise SimError(f"некоректний JSON у {path}: {error}") from None
    except KeyError as error:
        raise SimError(f"у {path} немає поля або метрики {error}") from None
    except (TypeError, ValueError) as error:
        raise SimError(f"некоректне значення метрики у {path}: {error}") from None


def read_float(name: str, default: float | None = None) -> float:
    raw = os.environ.get(name)
    if raw is None and default is None:
        raise SimError(f"не задано змінну середовища {name}")
    try:
        return float(raw) if raw is not None else default
    except ValueError:
        raise SimError(f"{name} має бути числом, отримано: {raw}") from None


def read_params() -> dict:
    rate = read_float("HOURLY_RATE")
    if not 35 <= rate <= 50:
        raise SimError(f"HOURLY_RATE має бути в межах 35-50, отримано: {rate}")
    return {"rate": rate, "overload": read_float("OVERLOAD_COEFF", 1.3), "discount": read_float("DISCOUNT_RATE", 0.01)}


def verdict_lines(rows: list[dict]) -> list[str]:
    month = payback_month(rows)
    final = rows[-1]["npv"]
    if month is None:
        return ["## 4. Вердикт", "", f"NPV не стає додатним за {MONTHS} місяців (NPV_{MONTHS} = {final:.2f}). Окупності немає.", "",
                "## 5. Quality Gate", "", f"**FAIL**. Попередження: погашення боргу не окупається за {MONTHS} місяців."]
    return ["## 4. Вердикт", "", f"Місяць окупності (Payback Period): {month}. NPV_{MONTHS} = {final:.2f}.", "",
            "## 5. Quality Gate", "", f"**PASS**: NPV > 0 за {MONTHS} місяців."]


def render(report: dict, params: dict, debt: float, cod: float, rows: list[dict]) -> str:
    table = [f"| {r['month']} | {r['factor']:.6f} | {r['effect']:.2f} | {r['npv']:.2f} |" for r in rows]
    return "\n".join([
        "# Financial Ledger", "",
        "## 1. Вхідні параметри", "",
        "| Параметр | Значення |", "|---|---|",
        f"| Project key | {report['key']} |", f"| ncloc | {report['ncloc']} |", f"| sqale_index, хв | {report['sqale_index']} |",
        f"| HOURLY_RATE | {params['rate']:g} |", f"| OVERLOAD_COEFF | {params['overload']:g} |", f"| DISCOUNT_RATE | {params['discount']:g} |", "",
        "## 2. Principal і Cost of Delay", "",
        f"- Principal = sqale_index / 60 * HOURLY_RATE * OVERLOAD_COEFF = {debt:.2f}",
        f"- Cost of Delay на місяць = ncloc / 100 * HOURLY_RATE = {cod:.2f}", "",
        "## 3. Таблиця по місяцях", "",
        "| Місяць | Коефіцієнт дисконтування | Щомісячний ефект | Кумулятивний NPV |", "|---|---|---|---|",
        *table, "", *verdict_lines(rows), ""])


def run(report_path: Path, output: Path) -> bool:
    report = load_report(report_path)
    params = read_params()
    debt = principal(report["sqale_index"], params["rate"], params["overload"])
    cod = cost_of_delay(report["ncloc"], params["rate"])
    rows = schedule(cod, debt, params["discount"])
    output.write_text(render(report, params, debt, cod, rows), encoding="utf-8")
    month = payback_month(rows)
    print(f"{report['key']}: Principal = {debt:.2f}, Cost of Delay = {cod:.2f}/міс")
    print(f"Payback Period: {month if month else 'немає'}; Quality Gate: {'PASS' if month else 'FAIL'}")
    print(f"Створено {output.name}")
    return month is not None


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        passed = run(Path(argv[1]), Path(argv[2]) if len(argv) == 3 else DEFAULT_LEDGER)
    except SimError as error:
        print(f"Помилка: {error}", file=sys.stderr)
        return 2
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
