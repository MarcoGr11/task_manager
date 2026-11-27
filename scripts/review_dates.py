#!/usr/bin/env python3
"""Check docs/**/*.md front matter: required fields, allowed status, overdue review_date.

Usage: python scripts/review_dates.py [--today YYYY-MM-DD] [--strict]
Prints overdue pages (review_date < today, status != deprecated).
Exit 1 on a missing or invalid field; with --strict also when a page is overdue.
"""
import argparse
import sys
from datetime import date
from pathlib import Path

REQUIRED = ("owner", "status", "review_date")
STATUSES = {"draft", "in-review", "published", "deprecated"}


def front_matter(text: str) -> dict:
    """Flat `key: value` pairs of the leading --- block (lists and nesting are ignored)."""
    if not text.startswith("---\n"):
        return {}
    block = text[4:text.find("\n---", 4)]
    pairs = (line.split(":", 1) for line in block.splitlines() if ":" in line and not line.startswith(" "))
    return {k.strip(): v.strip().strip('"') for k, v in pairs}


def problems(meta: dict) -> list[str]:
    found = [f"немає поля {key}" for key in REQUIRED if not meta.get(key)]
    if meta.get("status") and meta["status"] not in STATUSES:
        found.append(f"недопустимий status {meta['status']}")
    if meta.get("review_date"):
        try:
            date.fromisoformat(meta["review_date"])
        except ValueError:
            found.append(f"review_date не ISO-дата: {meta['review_date']}")
    return found


def scan(today: date) -> tuple[int, int, list[str], list[str]]:
    invalid, overdue, deprecated, total = 0, [], [], 0
    for page in sorted(Path("docs").rglob("*.md")):
        total += 1
        meta = front_matter(page.read_text(encoding="utf-8"))
        issues = problems(meta)
        for issue in issues:
            print(f"ERROR {page}: {issue}")
        invalid += bool(issues)
        if issues:
            continue
        if meta["status"] == "deprecated":
            deprecated.append(f"{page} -> {meta.get('redirect_to', 'без переспрямування')}")
        elif date.fromisoformat(meta["review_date"]) < today:
            overdue.append(f"{page}: review_date {meta['review_date']}, owner {meta['owner']}")
    return total, invalid, overdue, deprecated


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--strict", action="store_true", help="fail on overdue pages too")
    args = parser.parse_args(argv)
    total, invalid, overdue, deprecated = scan(args.today)
    print(f"Сьогодні {args.today}. Сторінок: {total}, з помилками front matter: {invalid}, прострочених: {len(overdue)}, deprecated: {len(deprecated)}")
    for line in overdue:
        print(f"OVERDUE {line}")
    for line in deprecated:
        print(f"DEPRECATED {line}")
    return 1 if invalid or (args.strict and overdue) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
