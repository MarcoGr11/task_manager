"""Centralized PII/secret sanitization for every log record (Lab 4, Task 1).

Logging policy:
  ALLOWED  ids (user_id, subject_id, actor_id), correlation_id, event/operation, result, timestamps
  MASKED   email -> a***@example.com, phone -> +**********67 (last 2 digits kept)
  REDACTED any field whose name contains password / token / secret / api_key -> [REDACTED]
"""
import logging
import re
import traceback

REDACTED = "[REDACTED]"

_SECRET_KEY = r"[\w-]*(?:password|passwd|token|secret|api[_-]?key)[\w-]*"
_SECRET_KEY_RE = re.compile(rf"^{_SECRET_KEY}$", re.IGNORECASE)
# key=value, key: value, "key": "value", 'key': 'value'  (plain text, JSON, Python repr)
_SECRET_PAIR_RE = re.compile(
    rf"""(?P<key>["']?{_SECRET_KEY}["']?\s*[:=]\s*)(?P<value>"[^"]*"|'[^']*'|[^\s,;}}&]+)""",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
# ponytail: digit-run heuristic (10-15 digits, or +country with spaces/dashes); a bare
# 10+ digit number such as a unix timestamp is masked too. Use phonenumbers lib if that matters.
_PHONE_RE = re.compile(r"\+\d(?:[\s-]?\d){9,14}\b|\b\d{10,15}\b")


def mask_email(match: re.Match) -> str:
    return f"{match.group(1)}***@{match.group(2)}"


def mask_phone(match: re.Match) -> str:
    phone = match.group(0)
    total = sum(c.isdigit() for c in phone)
    seen = 0
    out = []
    for c in phone:
        if c.isdigit():
            seen += 1
            out.append(c if seen > total - 2 else "*")
        elif c == "+":
            out.append(c)
    return "".join(out)


def _redact_pair(match: re.Match) -> str:
    value = match.group("value")
    quote = value[0] if value[0] in "\"'" else ""
    return f"{match.group('key')}{quote}{REDACTED}{quote}"


def sanitize_text(text: str) -> str:
    text = _SECRET_PAIR_RE.sub(_redact_pair, text)
    text = _EMAIL_RE.sub(mask_email, text)
    return _PHONE_RE.sub(mask_phone, text)


def sanitize(value):
    """Recursively sanitize dicts/lists/strings; secret-named keys are redacted whatever the value."""
    if isinstance(value, dict):
        return {k: REDACTED if _SECRET_KEY_RE.match(str(k)) else sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(sanitize(v) for v in value)
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, BaseException):
        return sanitize_text(str(value))
    return value


class SensitiveDataFilter(logging.Filter):
    """Rewrites a record in place: message, args, exception text and stack info."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            record.args = sanitize(record.args)  # tuple, or a single dict for %(name)s formatting
        try:
            record.msg = sanitize_text(record.getMessage())
            record.args = None
        except (TypeError, ValueError):  # broken format string: still never leak the raw text
            record.msg = sanitize_text(str(record.msg))
        if record.exc_info and not record.exc_text:
            record.exc_text = sanitize_text("".join(traceback.format_exception(*record.exc_info)).rstrip("\n"))
        if record.stack_info:
            record.stack_info = sanitize_text(record.stack_info)
        return True


_installed = False


def install_sensitive_data_filter() -> None:
    """Apply SensitiveDataFilter to EVERY record of EVERY logger in the process.

    A filter added to the root *logger* would not see records propagated from child
    loggers (tasks.api, uvicorn, httpx...), so the filter is hooked into the LogRecord
    factory instead: every handler (console, file, pytest caplog) gets clean records.
    """
    global _installed
    if _installed:
        return
    base_factory = logging.getLogRecordFactory()
    sensitive_filter = SensitiveDataFilter()

    def factory(*args, **kwargs):
        record = base_factory(*args, **kwargs)
        sensitive_filter.filter(record)
        return record

    logging.setLogRecordFactory(factory)
    _installed = True


if __name__ == "__main__":
    # Live demo: python -m tasks.logging_utils   (synthetic values only)
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    install_sensitive_data_filter()
    log = logging.getLogger("demo")
    log.info("User demo.user@example.com logged in from +380501234567 with password=Synthetic-Pass-1")  # gitleaks:allow (synthetic demo value)
    log.info(json.dumps({"event": "login", "email": "demo.user@example.com", "access_token": "tok-123", "correlation_id": "c-1"}))
    try:
        raise ValueError({"user": {"email": "demo.user@example.com", "api_key": "key-123"}})
    except ValueError:
        log.exception("Import failed")
