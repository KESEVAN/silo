import dataclasses

import pytest

from silo.core.message import Message


def test_message_is_immutable():
    msg = Message(sender="mechanical", recipient="judiciary", payload={"x": 1})
    with pytest.raises(dataclasses.FrozenInstanceError):
        msg.sender = "farmers"  # type: ignore[misc]


def test_message_ids_are_unique_per_instance():
    a = Message(sender="a", recipient="b", payload={})
    b = Message(sender="a", recipient="b", payload={})
    assert a.message_id != b.message_id
    assert a.timestamp > 0


def test_message_priority_defaults_to_zero():
    msg = Message(sender="a", recipient="b", payload={})
    assert msg.priority == 0
