"""DecisionMaker interface -- what an Agent asks to turn context into a
Decision.

A rule-based implementation can answer instantly with an if/else. An
LLM-backed implementation can call out to OpenRouter (see silo.llm). Agent
and PorterAgent depend only on this interface, never on either concrete
implementation -- this is the same PDP/PEP-style seam the roadmap uses for
PolicyEngine in Iteration 2, applied one iteration early because the
reasoning core is exactly the kind of thing you want to be able to swap
providers on without a rewrite.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .agent import Decision


class DecisionMaker(ABC):
    @abstractmethod
    def decide(self, context: dict[str, Any], available_tools: list[str]) -> Decision:
        raise NotImplementedError
