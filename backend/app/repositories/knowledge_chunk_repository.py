from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk


class KnowledgeChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_many(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        self.db.add_all(chunks)
        self.db.commit()
        for chunk in chunks:
            self.db.refresh(chunk)
        return chunks

    def list_all(self) -> list[KnowledgeChunk]:
        statement = select(KnowledgeChunk).order_by(
            KnowledgeChunk.doc_id.asc(),
            KnowledgeChunk.chunk_index.asc(),
            KnowledgeChunk.id.asc(),
        )
        return list(self.db.scalars(statement).all())

    def list_by_doc_id(self, doc_id: int) -> list[KnowledgeChunk]:
        statement = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.doc_id == doc_id)
            .order_by(KnowledgeChunk.chunk_index.asc(), KnowledgeChunk.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def save(self, chunk: KnowledgeChunk) -> KnowledgeChunk:
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def delete_by_doc_id(self, doc_id: int) -> None:
        statement = delete(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc_id)
        self.db.execute(statement)
        self.db.commit()
