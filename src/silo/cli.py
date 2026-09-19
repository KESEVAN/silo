"""Entry point: `python -m silo.cli` or the `silo-run` console script.

Wires one PorterAgent end to end. Uses the OpenRouter-backed
LLMDecisionMaker when OPENROUTER_API_KEY is set, otherwise falls back to a
rule-based one -- the DecisionMaker implementation is the only thing that
changes between the two runs.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from silo.agents.porter_agent import PorterAgent
from silo.agents.rule_based_decision_maker import RuleBasedDecisionMaker
from silo.core.decision_maker import DecisionMaker
from silo.tools.log_tool import LogTool
from silo.tools.read_tool import ReadTool
from silo.tools.send_tool import SendTool


def build_decision_maker() -> DecisionMaker:
    load_dotenv()
    if os.getenv("OPENROUTER_API_KEY"):
        from silo.llm.decision_maker import LLMDecisionMaker
        from silo.llm.openrouter import OpenRouterClient

        print("[silo] OPENROUTER_API_KEY found -- using the LLM-backed DecisionMaker.")
        return LLMDecisionMaker(OpenRouterClient())

    print(
        "[silo] OPENROUTER_API_KEY not set -- running with the rule-based "
        "fallback DecisionMaker. Copy .env.example to .env and add a free "
        "OpenRouter key (https://openrouter.ai/keys) to try the LLM-backed one."
    )
    return RuleBasedDecisionMaker()


def main() -> None:
    inbox = [{"from": "mechanical", "note": "pressure reading nominal"}]
    tools = {
        "log": LogTool(),
        "read": ReadTool(inbox=list(inbox)),
        "send": SendTool(),
    }

    porter = PorterAgent(tools=tools, decision_maker=build_decision_maker())
    context = porter.perceive(inbox)
    decision = porter.decide(context)
    result = porter.act(decision)

    print(f"[silo] decision: {decision}")
    print(f"[silo] result:   {result}")


if __name__ == "__main__":
    main()
