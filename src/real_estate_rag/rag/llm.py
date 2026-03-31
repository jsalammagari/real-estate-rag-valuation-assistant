"""LLM adapters for Story 6 RAG orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from urllib import request


class LlmClient:
    """LLM adapter interface."""

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class StubLlmClient(LlmClient):
    """Deterministic local client for CI/tests."""

    prefix: str = "STUB_ANSWER"

    def generate(self, prompt: str) -> str:
        return f"{self.prefix}: grounded response generated from provided context."


@dataclass(frozen=True)
class RemoteHTTPLlmClient(LlmClient):
    """Optional remote HTTP LLM adapter."""

    endpoint: str
    model: str
    api_key: str
    timeout_seconds: int = 30

    def generate(self, prompt: str) -> str:
        payload = json.dumps({"model": self.model, "prompt": prompt}).encode("utf-8")
        req = request.Request(
            url=self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:  # nosec B310
            body = resp.read().decode("utf-8")
            data = json.loads(body)
        text = data.get("text")
        if not isinstance(text, str):
            raise ValueError("Remote LLM response missing string field 'text'")
        return text


def create_llm_client_from_env(
    provider: str,
    *,
    endpoint: str = "",
    model: str = "",
    api_key: str = "",
) -> LlmClient:
    """Factory for selecting an LLM client."""
    if provider == "stub":
        return StubLlmClient()
    if provider == "remote_http":
        if not endpoint or not model or not api_key:
            raise ValueError("remote_http provider requires endpoint, model, and api_key")
        return RemoteHTTPLlmClient(endpoint=endpoint, model=model, api_key=api_key)
    raise ValueError(f"Unsupported LLM provider: {provider}")
