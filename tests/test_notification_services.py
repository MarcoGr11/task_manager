"""Public behaviour of the e-mail notification service across all its layers."""
import pytest

from tasks.notification_services import EmailNotificationService

SENDER = "noreply@example.com"


def make_email(sender=SENDER):
    return EmailNotificationService("mail", sender)


@pytest.fixture
def email():
    service = make_email()
    service.start()
    return service


def test_start_requires_sender():
    with pytest.raises(RuntimeError):
        make_email(None).start()


def test_start_and_stop_are_recorded(email):
    email.stop()
    assert not email.is_running()
    assert email.history() == ["start", "stop"]


def test_reset_history(email):
    email.reset_history()
    assert email.history() == []


def test_record_with_detail(email):
    email.record("custom", "x")
    assert email.history()[-1] == "custom:x"


def test_describe_includes_state_and_sender(email):
    assert email.describe() == f"mail running=True sender={SENDER}"


def test_send_renders_email_and_records(email):
    entry = email.send("a@example.com", "  Hello\nworld ")
    assert entry["body"] == f"From: {SENDER}\nSubject: Hello\n\nHello\nworld"
    assert email.history()[-1] == "sent:a@example.com"
    assert email.sent_count() == 1


def test_send_requires_running_service():
    with pytest.raises(RuntimeError):
        make_email().send("a@example.com", "hi")


def test_send_rejects_bad_recipient(email):
    with pytest.raises(ValueError):
        email.send("nobody", "hi")


@pytest.mark.parametrize("message", ["   ", "x" * 201])
def test_send_rejects_invalid_message(email, message):
    with pytest.raises(ValueError):
        email.send("a@example.com", message)
    assert email.sent_count() == 0


def test_send_many_applies_email_rules(email):
    assert [e["recipient"] for e in email.send_many(["a@x.io", "b@x.io"], "hi")] == ["a@x.io", "b@x.io"]
    with pytest.raises(ValueError):
        email.send_many(["bad"], "hi")


def test_cc_is_attached_to_sent_entry(email):
    email.add_cc("c@example.com")
    assert email.send("a@example.com", "hi")["cc"] == ["c@example.com"]
    assert email.last_sent()["cc"] == ["c@example.com"]


def test_last_sent_has_channel_or_none(email):
    assert email.last_sent() is None
    email.send("a@example.com", "hi")
    assert email.last_sent()["channel"] == "email"


def test_clear_sent_also_clears_cc(email):
    email.add_cc("c@example.com")
    email.send("a@example.com", "hi")
    email.clear_sent()
    assert (email.sent_count(), email.cc_list(), email.history()[-1]) == (0, [], "cleared")


def test_clear_cc(email):
    email.add_cc("c@example.com")
    email.clear_cc()
    assert email.cc_list() == []


def test_set_and_get_sender(email):
    email.set_sender("other@example.com")
    assert email.get_sender() == "other@example.com"
    assert email.preview("hi").startswith("From: other@example.com")


def test_subject_is_first_line_truncated(email):
    assert email.subject_for("y" * 50 + "\nsecond") == "y" * 40
