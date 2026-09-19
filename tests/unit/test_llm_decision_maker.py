import pytest

from silo.core.agent import Decision
from silo.llm.decision_maker import LLMDecisionMaker


class FakeCompleter:
    def __init__(self, response: str) -> None:
        self._response = response
        self.last_messages = None

    def complete(self, messages, *, response_format_json: bool = False) -> str:
        self.last_messages = messages
        return self._response


def test_decide_parses_valid_json_into_a_decision():
    completer = FakeCompleter(
        '{"tool_name": "log", "args": {"message": "hi"}, "reasoning": "why not"}'
    )
    maker = LLMDecisionMaker(completer)

    decision = maker.decide({"pending_messages": []}, available_tools=["log", "read"])

    assert decision == Decision(tool_name="log", args={"message": "hi"}, reasoning="why not")


def test_decide_rejects_a_tool_the_model_invented():
    completer = FakeCompleter('{"tool_name": "nuke", "args": {}}')
    maker = LLMDecisionMaker(completer)

    with pytest.raises(ValueError):
        maker.decide({}, available_tools=["log", "read"])


def test_decide_rejects_invalid_json():
    completer = FakeCompleter("not json")
    maker = LLMDecisionMaker(completer)

    with pytest.raises(ValueError):
        maker.decide({}, available_tools=["log"])
