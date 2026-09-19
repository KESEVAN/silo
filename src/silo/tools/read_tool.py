"""ReadTool -- reads from an in-memory inbox. Stand-in until Iteration 1's
MessageQueue gives agents something real to read from.
"""

from __future__ import annotations

from typing import Any

from silo.core.tool import Tool


class ReadTool(Tool):
    name = "read"

    def __init__(self, inbox: list[dict[str, Any]] | None = None) -> None:
        self._inbox = inbox if inbox is not None else []

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self._inbox:
            return {"tool": self.name, "status": "empty"}
        item = self._inbox.pop(0)
        return {"tool": self.name, "status": "ok", "item": item}
