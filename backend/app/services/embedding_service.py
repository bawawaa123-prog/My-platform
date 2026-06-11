from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import get_settings


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Return a dense vector for a single text input."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    @abstractmethod
    def build_embedding_id(self, text: str) -> str:
        """Return a stable identifier for the text embedding."""


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 64):
        if dimension <= 0:
            raise ValueError("Embedding dimension must be greater than 0")
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        normalized = self._normalize_text(text)
        if not normalized:
            return [0.0] * self.dimension

        values: list[float] = []
        counter = 0
        while len(values) < self.dimension:
            digest = hashlib.sha256(f"{normalized}:{counter}".encode("utf-8")).digest()
            for index in range(0, len(digest), 4):
                chunk = digest[index : index + 4]
                raw_value = int.from_bytes(chunk, byteorder="big", signed=False)
                scaled_value = (raw_value / 4294967295.0) * 2.0 - 1.0
                values.append(round(scaled_value, 6))
                if len(values) >= self.dimension:
                    break
            counter += 1
        return values

    def build_embedding_id(self, text: str) -> str:
        normalized = self._normalize_text(text)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"fake-{digest}"

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.split()).strip()


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, model: str):
        self.model = model

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError(
            "OpenAI-compatible embedding provider is reserved for a later step. "
            "Set EMBEDDING_PROVIDER=fake for local development."
        )

    def build_embedding_id(self, text: str) -> str:
        normalized = " ".join(text.split()).strip()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"openai-compatible:{self.model}:{digest}"


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()

    if settings.embedding_provider == "fake":
        return FakeEmbeddingProvider(dimension=settings.embedding_dimension)

    if settings.embedding_provider == "openai-compatible":
        return OpenAICompatibleEmbeddingProvider(model=settings.embedding_model)

    raise ValueError(
        "Unsupported EMBEDDING_PROVIDER. "
        "Expected one of: fake, openai-compatible."
    )
