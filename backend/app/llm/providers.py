"""Concrete LLM providers. Keys come from household settings or process env — never from git."""

import json
from typing import Any

import httpx

from app.llm.base import CategorizationResult, FileInterpretationResult, LLMProvider, StubLLMProvider


class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model

    def interpret_file(self, structural_summary: dict[str, Any]) -> FileInterpretationResult:
        prompt = (
            "You interpret financial file structures. Return ONLY valid JSON matching the "
            "required schema. Prefer existing column meanings. Do not invent rows.\n\n"
            f"Structural summary:\n{json.dumps(structural_summary)[:12000]}"
        )
        data = self._chat_json(prompt, FileInterpretationResult.model_json_schema())
        return FileInterpretationResult.model_validate(data)

    def categorize(
        self,
        event_context: dict[str, Any],
        categories: list[dict[str, Any]],
    ) -> CategorizationResult:
        prompt = (
            "Categorize one household financial event. Prefer an existing category/subcategory. "
            "Never create a new category unless no existing one fits. Return ONLY JSON.\n\n"
            f"Event:\n{json.dumps(event_context)}\n\n"
            f"Categories:\n{json.dumps(categories)[:12000]}"
        )
        data = self._chat_json(prompt, CategorizationResult.model_json_schema())
        return CategorizationResult.model_validate(data)

    def _chat_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a careful financial data interpreter. "
                            "Respond with a single JSON object only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest"):
        self.api_key = api_key
        self.model_name = model

    def interpret_file(self, structural_summary: dict[str, Any]) -> FileInterpretationResult:
        # Fall back through OpenAI-compatible JSON extraction pattern via Anthropic Messages API.
        prompt = (
            "Return ONLY JSON for this financial file structural summary.\n"
            f"{json.dumps(structural_summary)[:12000]}"
        )
        data = self._messages_json(prompt)
        return FileInterpretationResult.model_validate(data)

    def categorize(
        self,
        event_context: dict[str, Any],
        categories: list[dict[str, Any]],
    ) -> CategorizationResult:
        prompt = (
            "Prefer existing categories. Return ONLY JSON categorization.\n"
            f"Event: {json.dumps(event_context)}\n"
            f"Categories: {json.dumps(categories)[:12000]}"
        )
        data = self._messages_json(prompt)
        return CategorizationResult.model_validate(data)

    def _messages_json(self, prompt: str) -> dict[str, Any]:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model_name,
                "max_tokens": 2000,
                "temperature": 0.1,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        text = response.json()["content"][0]["text"]
        start = text.find("{")
        end = text.rfind("}")
        return json.loads(text[start : end + 1])


def build_llm_provider(
    *,
    provider: str | None,
    model: str | None,
    api_key: str | None,
) -> LLMProvider:
    name = (provider or "stub").lower()
    if name in {"", "stub"} or not api_key:
        return StubLLMProvider()
    if name == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4o-mini")
    if name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model or "claude-3-5-haiku-latest")
    # Gemini and local can be added the same way; use stub until configured.
    if name in {"gemini", "google", "local"}:
        return StubLLMProvider()
    return StubLLMProvider()
