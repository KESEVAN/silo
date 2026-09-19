from typing import Any

import pytest

from silo.agents.porter_agent import PorterAgent
from silo.core.agent import Decision
from silo.core.decision_maker import DecisionMaker
from silo.core.tool import Tool


class FakeTool(Tool):
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(args)
        return {"tool": self.name, "status": "ok", "echo": args}


class FixedDecisionMaker(DecisionMaker):
    def __init__(self, decision: Decision) -> None:
        self._decision = decision

    def decide(self, context: dict[str, Any], available_tools: list[str]) -> Decision:
        return self._decision


def make_porter(decision: Decision, tool: Tool) -> PorterAgent:
    return PorterAgent(tools={tool.name: tool}, decision_maker=FixedDecisionMaker(decision))


def test_act_invokes_the_right_tool_with_the_right_args_and_records_memory():
    tool = FakeTool()
    decision = Decision(tool_name="fake", args={"x": 1})
    porter = make_porter(decision, tool)

    result = porter.act(decision)

    assert tool.calls == [{"x": 1}]
    assert result == {"tool": "fake", "status": "ok", "echo": {"x": 1}}
    assert porter.memory == [result]


@pytest.mark.parametrize(
    "inbox,expected_pending_count",
    [
        ([], 0),
        ([{"from": "mechanical"}], 1),
        ([{"from": "mechanical"}, {"from": "farmers"}], 2),
    ],
)
def test_perceive_carries_pending_messages_into_context(inbox, expected_pending_count):
    tool = FakeTool()
    porter = make_porter(Decision(tool_name="fake"), tool)
    context = porter.perceive(inbox)
    assert len(context["pending_messages"]) == expected_pending_count


def test_decide_delegates_to_the_injected_decision_maker():
    tool = FakeTool()
    decision = Decision(tool_name="fake", args={"reason": "test"})
    porter = make_porter(decision, tool)
    assert porter.decide({"pending_messages": []}) is decision
