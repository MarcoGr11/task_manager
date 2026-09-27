"""Controllable mock of the external notification service (fault injection)."""
import asyncio
from typing import Literal

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Mock Notifier")
state = {"mode": "ok"}
TIMEOUT_DELAY_SECONDS = 10


@app.post("/_control")
def control(mode: Literal["ok", "timeout", "error"]) -> dict:
    state["mode"] = mode
    return state


@app.post("/notify")
async def notify(payload: dict) -> dict:
    if state["mode"] == "error":
        raise HTTPException(status_code=503, detail="Notifier unavailable")
    if state["mode"] == "timeout":
        await asyncio.sleep(TIMEOUT_DELAY_SECONDS)
    return {"status": "sent", "task_id": payload.get("id")}
