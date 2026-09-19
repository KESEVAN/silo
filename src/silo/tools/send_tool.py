"""SendTool -- the only way an agent is allowed to reach another agent.
Iteration 0 stubs delivery in-process via an injected callback; Iteration 1
replaces the callback with a real MessageQueue so nothing here has to
change.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from silo.core.tool import Tool


class SendTool(Tool):
    name = "send"

    def __init__(self, deliver: Callable[[dict[str, Any]], None] | None = None) -> None:
        # Injected delivery function -- defaults to a no-op sink so the
        # tool works standalone in tests and the Iteration 0 CLI.
        self._deliver = deliver or (lambda _msg: None)
        self._sent: list[dict[str, Any]] = []

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        recipient = args.get("recipient")
        payload = args.get("payload", {})
        if not recipient:
            return {"tool": self.name, "status": "error", "reason": "missing recipient"}

        message = {"recipient": recipient, "payload": payload}
        self._sent.append(message)
        self._deliver(message)
        return {"tool": self.name, "status": "ok", "message": message}

    @property
    def sent(self) -> list[dict[str, Any]]:
        return list(self._sent)
