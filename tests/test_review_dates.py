import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("review_dates", Path(__file__).parents[1] / "scripts" / "review_dates.py")
review_dates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_dates)

PAGE = "---\ntitle: \"A: b\"\nowner: x\nstatus: {status}\nreview_date: {review}\ntags:\n  - api\n---\n\n# A\n"


def write(tmp_path, name, status="published", review="2027-01-01"):
    path = tmp_path / "docs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PAGE.format(status=status, review=review), encoding="utf-8")


def test_front_matter_parses_flat_keys():
    meta = review_dates.front_matter(PAGE.format(status="draft", review="2027-01-01"))
    assert meta == {"title": "A: b", "owner": "x", "status": "draft", "review_date": "2027-01-01", "tags": ""}


def test_overdue_strict_and_deprecated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "fresh.md", review="2027-06-01")
    write(tmp_path, "old.md", review="2026-01-01")
    write(tmp_path, "gone.md", status="deprecated", review="2026-01-01")
    assert review_dates.main(["--today", "2026-11-27"]) == 0
    assert review_dates.main(["--today", "2026-11-27", "--strict"]) == 1
    total, invalid, overdue, deprecated = review_dates.scan(review_dates.date(2026, 11, 27))
    assert (total, invalid, len(overdue), len(deprecated)) == (3, 0, 1, 1)


def test_invalid_status_and_missing_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write(tmp_path, "bad.md", status="final")
    (tmp_path / "docs" / "none.md").write_text("# no front matter\n", encoding="utf-8")
    assert review_dates.main(["--today", "2026-11-27"]) == 1
