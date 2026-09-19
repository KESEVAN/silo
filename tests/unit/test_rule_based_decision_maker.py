import pytest

from silo.agents.rule_based_decision_maker import RuleBasedDecisionMaker


@pytest.mark.parametrize(
    "context,available_tools,expected_tool",
    [
        ({"pending_messages": [{"from": "a"}]}, ["read", "log"], "read"),
        ({"pending_messages": []}, ["read", "log"], "log"),
        ({"pending_messages": [{"from": "a"}, {"from": "b"}]}, ["log"], "log"),
        ({"pending_messages": []}, ["send"], "send"),
        ({}, ["read", "log"], "log"),
    ],
)
def test_decide_picks_expected_tool_for_context(context, available_tools, expected_tool):
    maker = RuleBasedDecisionMaker()
    decision = maker.decide(context, available_tools)
    assert decision.tool_name == expected_tool
