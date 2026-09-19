"""LogTool -- writes a line to an in-memory audit trail. Stand-in for
silo.audit.event_log until Iteration 4 gives departments a real
append-only log.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from silo.core.tool import Tool


class LogTool(Tool):
    name = "log"

    def __init__(self) -> None:
        self._entries: list[str] = []

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        message = args.get("message", "")
        line = f"{datetime.now(UTC).isoformat()} | {message}"
        self._entries.append(line)
        return {"tool": self.name, "status": "ok", "line": line}

    @property
    def entries(self) -> list[str]:
        return list(self._entries)
