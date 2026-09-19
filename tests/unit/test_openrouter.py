import httpx
import pytest

from silo.llm.config import LLMConfig
from silo.llm.openrouter import OpenRouterClient, OpenRouterError


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
            response = httpx.Response(self.status_code, request=request, text=self.text)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


def test_missing_api_key_raises_before_any_request():
    with pytest.raises(OpenRouterError):
        OpenRouterClient(LLMConfig(api_key=None))


def test_complete_returns_message_content_on_success(monkeypatch):
    def fake_post(url, **kwargs):
        assert "chat/completions" in url
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        return _FakeResponse(200, {"choices": [{"message": {"content": "hello"}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    client = OpenRouterClient(LLMConfig(api_key="test-key"))
    result = client.complete(messages=[{"role": "user", "content": "hi"}])
    assert result == "hello"


def test_complete_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse(500, {"error": "boom"}))
    client = OpenRouterClient(LLMConfig(api_key="test-key"))
    with pytest.raises(OpenRouterError):
        client.complete(messages=[{"role": "user", "content": "hi"}])


def test_complete_raises_on_unexpected_response_shape(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse(200, {"unexpected": True}))
    client = OpenRouterClient(LLMConfig(api_key="test-key"))
    with pytest.raises(OpenRouterError):
        client.complete(messages=[{"role": "user", "content": "hi"}])
