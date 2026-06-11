from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    chunk_size: int = 800
    overlap: int = 100


class ChunkingService:
    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()

    def split_text(self, text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []

        chunk_size = self.config.chunk_size
        overlap = self.config.overlap
        step = max(1, chunk_size - overlap)

        chunks: list[str] = []
        start = 0
        length = len(normalized)

        while start < length:
            end = min(length, start + chunk_size)
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= length:
                break
            start += step

        return chunks
