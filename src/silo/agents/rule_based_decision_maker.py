"""RuleBasedDecisionMaker -- a trivial, dependency-free DecisionMaker.

Exists so the simulation runs out of the box with zero configuration, and
so PorterAgent's swap from rules to an LLM is a one-line change instead of
a rewrite -- compare the two branches in silo.cli.build_decision_maker().
"""

from __future__ import annotations

from typing import Any

from silo.core.agent import Decision
from silo.core.decision_maker import DecisionMaker


class RuleBasedDecisionMaker(DecisionMaker):
    def decide(self, context: dict[str, Any], available_tools: list[str]) -> Decision:
        pending = context.get("pending_messages") or []

        if pending and "read" in available_tools:
            return Decision(tool_name="read", args={}, reasoning="inbox is non-empty")

        if "log" in available_tools:
            return Decision(
                tool_name="log",
                args={"message": "idle -- no pending messages"},
                reasoning="nothing to act on",
            )

        return Decision(tool_name=available_tools[0], args={}, reasoning="fallback: first tool")
