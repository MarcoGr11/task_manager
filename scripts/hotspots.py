"""Lab 7: Hotspots matrix = complexity (radon cc) x churn (git log).

Usage: python scripts/hotspots.py complexity.json churn.txt hotspots.csv
  complexity.json - output of `radon cc -j -s tasks`
  churn.txt       - output of `git log --format=format: --name-only | egrep -v '^$' | sort | uniq -c | sort -nr`

Thresholds are fixed here, before looking at any result:
  complexity is HIGH if the file's max CC (functions/methods) > CC_LIMIT (same limit as the pre-commit gate)
  churn is HIGH if the file's commit count > median commit count over the analysed files
Only tasks/*.py files present in complexity.json are analysed (docs moved to doc/ are noise).
"""
import csv
import json
import statistics
import sys

CC_LIMIT = 10
CATEGORIES = {
    (True, True): "High Risk (Hotspot)",
    (True, False): "Sleeping Danger",
    (False, True): "Active Development",
    (False, False): "Stable",
}


def read_churn(path):
    churn = {}
    for line in open(path):
        count, _, name = line.strip().partition(" ")
        if count.isdigit():
            churn[name] = int(count)
    return churn


def build(complexity, churn):
    rows = []
    for path, blocks in sorted(complexity.items()):
        if not (path.startswith("tasks/") and path.endswith(".py")):
            continue
        ccs = [b["complexity"] for b in blocks if b["type"] != "class"]  # class CC is an aggregate of its methods
        rows.append({"file": path, "max_cc": max(ccs, default=0),
                     "avg_cc": round(statistics.mean(ccs), 2) if ccs else 0.0,
                     "functions": len(ccs), "commits": churn.get(path, 0)})
    median = statistics.median(r["commits"] for r in rows)
    for r in rows:
        r["cc_high"] = r["max_cc"] > CC_LIMIT
        r["churn_high"] = r["commits"] > median
        r["category"] = CATEGORIES[(r["cc_high"], r["churn_high"])]
    return rows, median


def main(complexity_path, churn_path, out_path):
    rows, median = build(json.load(open(complexity_path)), read_churn(churn_path))
    rows.sort(key=lambda r: (-r["commits"] * r["max_cc"], r["file"]))
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"thresholds: max CC > {CC_LIMIT}; commits > median ({median}) over {len(rows)} files")
    print(f"{'file':28} {'maxCC':>5} {'avgCC':>6} {'commits':>7}  category")
    for r in rows:
        print(f"{r['file']:28} {r['max_cc']:5} {r['avg_cc']:6} {r['commits']:7}  {r['category']}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
