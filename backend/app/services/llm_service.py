from __future__ import annotations

import json
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any

from app.core.config import get_settings


class LLMGenerationError(RuntimeError):
    """Raised when an LLM request or response parsing step fails."""


class LLMClient(ABC):
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate plain text from the LLM."""

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Generate a JSON object from the LLM."""


class MockLLMClient(LLMClient):
    def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        normalized_prompt = " ".join(prompt.split()).strip()
        return f"[MOCK:{temperature:.1f}] {normalized_prompt[:400]}"

    def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        normalized_prompt = " ".join(prompt.split()).strip()
        return {
            "provider": "mock",
            "status": "ok",
            "summary": normalized_prompt[:200],
            "system_prompt_used": bool(system_prompt),
        }


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30.0,
    ) -> None:
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._build_messages(prompt, system_prompt=system_prompt),
                temperature=temperature,
            )
        except Exception as exc:  # pragma: no cover - depends on provider/network
            raise LLMGenerationError(f"LLM text generation failed: {exc}") from exc

        content = self._extract_text_content(response)
        if not content:
            raise LLMGenerationError("LLM text generation returned an empty response")
        return content

    def generate_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        enhanced_system_prompt = self._build_json_system_prompt(system_prompt)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self._build_messages(prompt, system_prompt=enhanced_system_prompt),
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        except Exception as exc:  # pragma: no cover - depends on provider/network
            raise LLMGenerationError(f"LLM JSON generation failed: {exc}") from exc

        content = self._extract_text_content(response)
        if not content:
            raise LLMGenerationError("LLM JSON generation returned an empty response")

        try:
            return json.loads(self._strip_markdown_fence(content))
        except json.JSONDecodeError as exc:
            raise LLMGenerationError(
                f"LLM JSON parsing failed: {exc.msg} at position {exc.pos}"
            ) from exc

    @staticmethod
    def _build_messages(prompt: str, *, system_prompt: str | None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def _build_json_system_prompt(system_prompt: str | None) -> str:
        json_instruction = "Return a valid JSON object only. Do not include markdown fences."
        if not system_prompt:
            return json_instruction
        return f"{system_prompt}\n\n{json_instruction}"

    @staticmethod
    def _extract_text_content(response: Any) -> str:
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, KeyError, TypeError) as exc:
            raise LLMGenerationError("LLM response does not contain message content") from exc

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(str(part.get("text", "")))
                elif hasattr(part, "text"):
                    text_parts.append(str(part.text))
            return "".join(text_parts).strip()

        return str(content).strip()

    @staticmethod
    def _strip_markdown_fence(content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```json"):
            stripped = stripped[7:]
        elif stripped.startswith("```"):
            stripped = stripped[3:]
        if stripped.endswith("```"):
            stripped = stripped[:-3]
        return stripped.strip()


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    settings = get_settings()

    if settings.llm_provider == "mock":
        return MockLLMClient()

    if settings.llm_provider == "openai-compatible":
        if not settings.llm_api_key:
            return MockLLMClient()
        return OpenAICompatibleLLMClient(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
        )

    raise ValueError(
        "Unsupported LLM_PROVIDER. Expected one of: mock, openai-compatible."
    )
