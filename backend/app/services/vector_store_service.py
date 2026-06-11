from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.models.knowledge_chunk import KnowledgeChunk
from app.services.embedding_service import get_embedding_provider


@dataclass
class VectorSearchHit:
    chunk_id: int
    doc_id: int
    score: float


class VectorStoreService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedding_provider = get_embedding_provider()
        self.index_path = Path(self.settings.vector_store_path).resolve()

    def rebuild_knowledge_index(self, chunks: list[KnowledgeChunk]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        entries = {}
        for chunk in chunks:
            entries[str(chunk.id)] = {
                "chunk_id": chunk.id,
                "doc_id": chunk.doc_id,
                "embedding_id": chunk.embedding_id,
                "vector": self.embedding_provider.embed_text(chunk.content),
            }

        payload = {
            "version": 1,
            "provider": self.settings.embedding_provider,
            "dimension": self.settings.embedding_dimension,
            "entries": entries,
        }
        self.index_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def search_knowledge_chunks(self, *, query: str, top_k: int) -> list[VectorSearchHit]:
        payload = self._load_index()
        entries = payload.get("entries", {})
        if not entries:
            return []

        query_vector = self.embedding_provider.embed_text(query)
        hits: list[VectorSearchHit] = []

        for raw_entry in entries.values():
            chunk_vector = raw_entry.get("vector", [])
            score = self._cosine_similarity(query_vector, chunk_vector)
            hits.append(
                VectorSearchHit(
                    chunk_id=int(raw_entry["chunk_id"]),
                    doc_id=int(raw_entry["doc_id"]),
                    score=round(score, 6),
                )
            )

        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]

    def _load_index(self) -> dict:
        if not self.index_path.exists():
            return {
                "version": 1,
                "provider": self.settings.embedding_provider,
                "dimension": self.settings.embedding_dimension,
                "entries": {},
            }

        return json.loads(self.index_path.read_text(encoding="utf-8"))

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0

        numerator = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))

        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0

        return numerator / (left_norm * right_norm)
