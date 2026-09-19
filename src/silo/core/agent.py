"""Agent primitive -- perceive / decide / act.

Every concrete agent in Silo (PorterAgent today, department agents in later
iterations) is built on this seam. decide() delegates to an injected
DecisionMaker rather than doing any reasoning itself, which is what keeps
this class testable without mocking a network call: swap in a fake
DecisionMaker and Agent's own logic (tool dispatch, memory) is exercised in
isolation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .tool import Tool


@dataclass(frozen=True)
class Decision:
    """What an Agent decided to do, before it does it."""

    tool_name: str
    args: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


class Agent(ABC):
    def __init__(self, tools: dict[str, Tool]) -> None:
        self._tools = tools  # injected, never hardcoded
        self._memory: list[dict[str, Any]] = []

    @property
    def memory(self) -> list[dict[str, Any]]:
        return list(self._memory)

    @abstractmethod
    def perceive(self, inbox: list[dict[str, Any]]) -> dict[str, Any]:
        """Turn raw inbox items into a context dict decide() can use."""
        raise NotImplementedError

    @abstractmethod
    def decide(self, context: dict[str, Any]) -> Decision:
        """Context in, Decision out."""
        raise NotImplementedError

    def act(self, decision: Decision) -> dict[str, Any]:
        tool = self._tools[decision.tool_name]  # depends on Tool interface
        result = tool.execute(decision.args)
        self._memory.append(result)
        return result
