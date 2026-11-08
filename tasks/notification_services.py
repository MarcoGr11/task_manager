"""Notification services composed through constructor injection."""

EMAIL_CHANNEL = "email"
MAX_EMAIL_LENGTH = 200


class BaseService:
    def __init__(self, name: str):
        self._name = name
        self._running = False
        self._events: list[str] = []

    def start(self) -> None:
        self._running = True
        self.record("start")

    def stop(self) -> None:
        self._running = False
        self.record("stop")

    def is_running(self) -> bool:
        return self._running

    def record(self, event: str, detail: str = "") -> None:
        self._events.append(f"{event}:{detail}" if detail else event)

    def history(self) -> list[str]:
        return list(self._events)

    def reset_history(self) -> None:
        self._events.clear()

    def describe(self) -> str:
        return f"{self._name} running={self._running}"


class NotificationService:
    def __init__(self, service: BaseService, channel: str):
        self._service = service
        self._channel = channel
        self._sent: list[dict] = []

    def start(self) -> None:
        self._service.start()

    def stop(self) -> None:
        self._service.stop()

    def is_running(self) -> bool:
        return self._service.is_running()

    def record(self, event: str, detail: str = "") -> None:
        self._service.record(event, detail)

    def history(self) -> list[str]:
        return self._service.history()

    def reset_history(self) -> None:
        self._service.reset_history()

    def describe(self) -> str:
        return self._service.describe()

    def validate(self, message: str) -> None:
        if not message.strip():
            raise ValueError("empty message")

    def render(self, message: str) -> str:
        return message.strip()

    def send(self, recipient: str, message: str) -> dict:
        if not self._service.is_running():
            raise RuntimeError("service is not running")
        self.validate(message)
        entry = {"recipient": recipient, "body": self.render(message)}
        self._sent.append(entry)
        self._service.record("sent", recipient)
        return entry

    def send_many(self, recipients: list[str], message: str) -> list[dict]:
        return [self.send(r, message) for r in recipients]

    def sent_count(self) -> int:
        return len(self._sent)

    def last_sent(self) -> dict | None:
        return self._sent[-1] if self._sent else None

    def clear_sent(self) -> None:
        self._sent.clear()
        self._service.record("cleared")


class EmailNotificationService:
    def __init__(self, notification: NotificationService, sender: str | None = None):
        self._notification = notification
        self._sender = sender
        self._cc: list[str] = []

    def start(self) -> None:
        if self._sender is None:
            raise RuntimeError("sender is not configured")
        self._notification.start()

    def stop(self) -> None:
        self._notification.stop()

    def is_running(self) -> bool:
        return self._notification.is_running()

    def record(self, event: str, detail: str = "") -> None:
        self._notification.record(event, detail)

    def history(self) -> list[str]:
        return self._notification.history()

    def reset_history(self) -> None:
        self._notification.reset_history()

    def describe(self) -> str:
        return f"{self._notification.describe()} sender={self._sender}"

    def validate(self, message: str) -> None:
        self._notification.validate(message)
        if len(message) > MAX_EMAIL_LENGTH:
            raise ValueError("message too long")

    def render(self, message: str) -> str:
        return f"From: {self._sender}\nSubject: {self.subject_for(message)}\n\n{message.strip()}"

    def send(self, recipient: str, message: str) -> dict:
        if "@" not in recipient:
            raise ValueError("invalid recipient")
        if not self._notification.is_running():
            raise RuntimeError("service is not running")
        self.validate(message)
        entry = self._notification.send(recipient, self.render(message))
        entry["cc"] = list(self._cc)
        return entry

    def send_many(self, recipients: list[str], message: str) -> list[dict]:
        return [self.send(r, message) for r in recipients]

    def sent_count(self) -> int:
        return self._notification.sent_count()

    def last_sent(self) -> dict | None:
        entry = self._notification.last_sent()
        return {**entry, "channel": EMAIL_CHANNEL} if entry else None

    def clear_sent(self) -> None:
        self._notification.clear_sent()
        self._cc.clear()

    def set_sender(self, sender: str) -> None:
        self._sender = sender

    def get_sender(self) -> str | None:
        return self._sender

    def add_cc(self, address: str) -> None:
        self._cc.append(address)

    def cc_list(self) -> list[str]:
        return list(self._cc)

    def clear_cc(self) -> None:
        self._cc.clear()

    def subject_for(self, message: str) -> str:
        return message.strip().splitlines()[0][:40]

    def preview(self, message: str) -> str:
        return self.render(message)
