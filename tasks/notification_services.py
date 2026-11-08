"""Three-level notification service hierarchy (Lab 8 audit baseline)."""

EMAIL_CHANNEL = "email"
MAX_EMAIL_LENGTH = 200


class BaseService:
    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.events: list[str] = []

    def start(self) -> None:
        self.running = True
        self.record("start")

    def stop(self) -> None:
        self.running = False
        self.record("stop")

    def is_running(self) -> bool:
        return self.running

    def record(self, event: str, detail: str = "", *, level: str) -> None:
        self.events.append(f"{event}:{detail}" if detail else event)

    def history(self) -> list[str]:
        return list(self.events)

    def reset_history(self) -> None:
        self.events.clear()

    def describe(self) -> str:
        return f"{self.name} running={self.running}"


class NotificationService(BaseService):
    def __init__(self, name: str, channel: str):
        super().__init__(name)
        self.channel = channel
        self.sent: list[dict] = []

    def validate(self, message: str) -> None:
        if not message.strip():
            raise ValueError("empty message")

    def render(self, message: str) -> str:
        return message.strip()

    def send(self, recipient: str, message: str) -> dict:
        if not self.is_running():
            raise RuntimeError("service is not running")
        self.validate(message)
        entry = {"recipient": recipient, "body": self.render(message)}
        self.sent.append(entry)
        self.record("sent", recipient)
        return entry

    def send_many(self, recipients: list[str], message: str) -> list[dict]:
        return [self.send(r, message) for r in recipients]

    def sent_count(self) -> int:
        return len(self.sent)

    def last_sent(self) -> dict | None:
        return self.sent[-1] if self.sent else None

    def clear_sent(self) -> None:
        self.sent.clear()
        self.record("cleared")


class EmailNotificationService(NotificationService):
    def __init__(self, name: str, sender: str | None = None):
        super().__init__(name, EMAIL_CHANNEL)
        self.sender = sender
        self.cc: list[str] = []

    def start(self) -> None:
        if self.sender is None:
            raise RuntimeError("sender is not configured")
        super().start()

    def describe(self) -> str:
        return f"{super().describe()} sender={self.sender}"

    def validate(self, message: str) -> None:
        super().validate(message)
        if len(message) > MAX_EMAIL_LENGTH:
            raise ValueError("message too long")

    def render(self, message: str) -> str:
        return f"From: {self.sender}\nSubject: {self.subject_for(message)}\n\n{message.strip()}"

    def send(self, recipient: str, message: str) -> dict:
        if "@" not in recipient:
            raise ValueError("invalid recipient")
        entry = super().send(recipient, message)
        entry["cc"] = list(self.cc)
        return entry

    def last_sent(self) -> dict | None:
        entry = super().last_sent()
        return {**entry, "channel": EMAIL_CHANNEL} if entry else None

    def clear_sent(self) -> None:
        super().clear_sent()
        self.cc.clear()

    def set_sender(self, sender: str) -> None:
        self.sender = sender

    def get_sender(self) -> str | None:
        return self.sender

    def add_cc(self, address: str) -> None:
        self.cc.append(address)

    def cc_list(self) -> list[str]:
        return list(self.cc)

    def clear_cc(self) -> None:
        self.cc.clear()

    def subject_for(self, message: str) -> str:
        return message.strip().splitlines()[0][:40]

    def preview(self, message: str) -> str:
        return self.render(message)
