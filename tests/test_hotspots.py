import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("hotspots", Path(__file__).parents[1] / "scripts" / "hotspots.py")
hotspots = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hotspots)


def _fn(cc):
    return {"type": "function", "complexity": cc}


def test_categories_use_max_cc_and_median_churn():
    complexity = {
        "tasks/a.py": [_fn(11), _fn(1)],                               # CC high, churn high -> Hotspot
        "tasks/b.py": [_fn(12)],                                       # CC high, churn low
        "tasks/c.py": [_fn(10), {"type": "class", "complexity": 30}],  # CC 10 is not > 10, class ignored
        "tasks/d.py": [_fn(2)],
        "doc/x.py": [_fn(50)],                                         # outside tasks/ -> ignored
    }
    churn = {"tasks/a.py": 5, "tasks/b.py": 1, "tasks/c.py": 4, "tasks/d.py": 2}  # median 3
    rows, median = hotspots.build(complexity, churn)
    assert median == 3
    assert {r["file"]: r["category"] for r in rows} == {
        "tasks/a.py": "High Risk (Hotspot)", "tasks/b.py": "Sleeping Danger",
        "tasks/c.py": "Active Development", "tasks/d.py": "Stable"}
