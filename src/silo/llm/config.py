"""Configuration for the OpenRouter-backed LLM client."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

# A free-tier Nemotron variant, picked as the starting model because
# OpenRouter serves it at zero cost. Free-tier slugs get retired or renamed
# periodically -- check https://openrouter.ai/models?max_price=0 and
# override via the OPENROUTER_MODEL env var if this one stops resolving.
DEFAULT_MODEL = "nvidia/nemotron-nano-9b-v2:free"


@dataclass(frozen=True)
class LLMConfig:
    api_key: str | None
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    temperature: float = 0.2
    max_tokens: int = 512
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> LLMConfig:
        return cls(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
            base_url=os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
        )
