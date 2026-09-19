"""Thin client for OpenRouter's chat-completions API.

Deliberately minimal: one public method, one responsibility. Swapping
providers later (Anthropic directly, a self-hosted vLLM box) means writing
another class with the same complete() signature -- nothing that depends on
the Completer shape (see silo.llm.decision_maker) needs to change.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import LLMConfig


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter can't be reached or returns something an
    Agent can't use."""


class OpenRouterClient:
    def __init__(self, config: LLMConfig | None = None) -> None:
        self._config = config or LLMConfig.from_env()
        if not self._config.api_key:
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not set. Get a free key at "
                "https://openrouter.ai/keys and put it in .env "
                "(see .env.example)."
            )

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        response_format_json: bool = False,
    ) -> str:
        """Send a chat-completion request, return the assistant's raw text."""
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = httpx.post(
                f"{self._config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                    # OpenRouter uses these to attribute free-tier traffic;
                    # harmless to omit, polite to send.
                    "HTTP-Referer": "https://github.com/",
                    "X-Title": "silo",
                },
                json=payload,
                timeout=self._config.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise OpenRouterError(
                f"OpenRouter returned {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise OpenRouterError(f"Unexpected OpenRouter response shape: {data}") from exc
