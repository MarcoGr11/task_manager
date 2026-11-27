"""CAPA CA-2 (RFC-001): replay delivers what it can and keeps the rest."""
import json

import httpx
import respx

from tasks import notifier_outbox
from tasks.notifier_resilient import NOTIFIER_URL


@respx.mock
def test_replay_delivers_and_keeps_failures(monkeypatch, tmp_path):
    for task_id in (1, 2, 3):
        notifier_outbox.append({"id": task_id, "title": f"t{task_id}"})
    respx.post(NOTIFIER_URL).mock(side_effect=lambda request: httpx.Response(
        503 if json.loads(request.content)["id"] == 2 else 200))

    assert notifier_outbox.replay() == (2, 1)
    assert [task["id"] for task in notifier_outbox.pending()] == [2]
    assert not notifier_outbox.outbox_path().with_name("outbox.jsonl.replaying").exists()


def test_replay_without_outbox_is_noop():
    assert notifier_outbox.replay() == (0, 0)

