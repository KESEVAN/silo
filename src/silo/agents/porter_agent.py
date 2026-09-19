"""PorterAgent -- Iteration 0's single agent.

Perceives an inbox, asks an injected DecisionMaker what to do, and acts
through whichever tools it was given. Nothing about this class knows
whether the DecisionMaker is a plain if/else or an LLM call over
OpenRouter -- that's the whole point of the seam.
"""

from __future__ import annotations

from typing import Any

from silo.core.agent import Agent, Decision
from silo.core.decision_maker import DecisionMaker
from silo.core.tool import Tool


class PorterAgent(Agent):
    def __init__(self, tools: dict[str, Tool], decision_maker: DecisionMaker) -> None:
        super().__init__(tools)
        self._decision_maker = decision_maker

    def perceive(self, inbox: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "pending_messages": inbox,
            "memory_tail": self.memory[-5:],
        }

    def decide(self, context: dict[str, Any]) -> Decision:
        return self._decision_maker.decide(context, available_tools=list(self._tools.keys()))
