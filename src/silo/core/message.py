"""Message schema -- the only thing two agents are allowed to know about
each other. See SILO_ROADMAP.md, Iteration 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from uuid import uuid4


@dataclass(frozen=True)
class Message:
    """An immutable envelope passed between agents via the Porter.

    Frozen so no department can mutate a message in flight -- a message
    that arrives is exactly the message that was sent.
    """

    sender: str
    recipient: str
    payload: dict
    priority: int = 0
    timestamp: float = field(default_factory=time)
    message_id: str = field(default_factory=lambda: uuid4().hex)
