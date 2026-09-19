"""LLMDecisionMaker -- turns Agent context into a Decision via an LLM call.

Wraps anything shaped like a Completer (OpenRouterClient today) behind the
DecisionMaker interface, so PorterAgent never touches an LLM client
directly. Swapping OpenRouter for a different provider, or going back to a
rule-based DecisionMaker for a deterministic test run, is a one-line change
at the call site -- see silo.cli.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from silo.core.agent import Decision
from silo.core.decision_maker import DecisionMaker


class Completer(Protocol):
    """What LLMDecisionMaker needs from an LLM client -- nothing more."""

    def complete(
        self, messages: list[dict[str, str]], *, response_format_json: bool = ...
    ) -> str: ...


_SYSTEM_PROMPT = (
    "You are the decision-making core of a Porter agent in a zero-trust "
    "message-routing simulation. Given a JSON context and a list of "
    "available tool names, respond with ONLY a JSON object of the shape "
    '{"tool_name": <one of the available tools>, "args": {...}, '
    '"reasoning": <short string>}. Never invent a tool name that is not '
    "in the available_tools list."
)


class LLMDecisionMaker(DecisionMaker):
    def __init__(self, client: Completer) -> None:
        self._client = client  # depends on the Completer protocol, not a concrete client

    def decide(self, context: dict[str, Any], available_tools: list[str]) -> Decision:
        user_prompt = json.dumps({"context": context, "available_tools": available_tools})
        raw = self._client.complete(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format_json=True,
        )
        parsed = self._parse(raw, available_tools)
        return Decision(
            tool_name=parsed["tool_name"],
            args=parsed.get("args", {}),
            reasoning=parsed.get("reasoning", ""),
        )

    @staticmethod
    def _parse(raw: str, available_tools: list[str]) -> dict[str, Any]:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Model did not return valid JSON: {raw!r}") from exc

        tool_name = parsed.get("tool_name")
        if tool_name not in available_tools:
            raise ValueError(f"Model chose an unavailable tool: {tool_name!r}")
        return parsed
