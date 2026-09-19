"""Tool interface -- the strategy pattern every agent capability implements.

An Agent never knows *how* a tool does its work, only that it can execute()
given a dict of arguments and return a dict result. This is the seam that
lets a LogTool, a SendTool, or a future network-calling tool sit behind the
exact same call site in Agent.act().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Something an Agent can invoke to act on the world."""

    name: str

    @abstractmethod
    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run the tool and return a result dict.

        Must not raise for expected failure modes -- return an error
        payload instead, so an Agent's control flow never has to
        special-case exceptions from its own tools.
        """
        raise NotImplementedError
