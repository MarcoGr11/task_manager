import pytest

from tasks.legacy_import import classify_row, run_migration_expression


def test_classify_row_defaults():
    result = classify_row({"title": "X"}, strict_mode=False, allow_empty_title=False, default_priority="LOW")
    assert result == {"priority": "LOW", "status": "todo", "tags": []}


def test_classify_row_missing_title_returns_none():
    assert classify_row({}, strict_mode=False, allow_empty_title=False, default_priority="LOW") is None


def test_classify_row_missing_title_strict_raises():
    with pytest.raises(ValueError):
        classify_row({}, strict_mode=True, allow_empty_title=False, default_priority="LOW")


def test_classify_row_bad_priority_strict_raises():
    with pytest.raises(ValueError):
        classify_row(
            {"title": "X", "priority": "URGENT"},
            strict_mode=True,
            allow_empty_title=False,
            default_priority="LOW",
        )


def test_run_migration_expression_known_filter():
    assert run_migration_expression("status_is_done", {"status": "done"}) is True


def test_run_migration_expression_unknown_raises():
    with pytest.raises(ValueError):
        run_migration_expression("os.system('rm -rf /')", {})


def test_classify_row_none_returns_none():
    assert classify_row(None, strict_mode=False, allow_empty_title=False, default_priority="LOW") is None


@pytest.mark.parametrize("row", [{"title": ""}, {"title": "X", "status": "blocked"}, {"title": "X", "tags": "a,b"}])
def test_classify_row_strict_invalid_raises(row):
    with pytest.raises(ValueError):
        classify_row(row, strict_mode=True, allow_empty_title=False, default_priority="LOW")


def test_classify_row_lenient_falls_back_to_defaults():
    row = {"title": "", "priority": "URGENT", "status": "blocked", "tags": "a,b"}
    result = classify_row(row, strict_mode=False, allow_empty_title=True, default_priority="MEDIUM")
    assert result == {"priority": "MEDIUM", "status": "todo", "tags": []}
