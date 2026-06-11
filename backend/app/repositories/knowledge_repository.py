from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_doc import KnowledgeDoc
from app.models.knowledge_chunk import KnowledgeChunk


class KnowledgeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, knowledge_doc: KnowledgeDoc) -> KnowledgeDoc:
        self.db.add(knowledge_doc)
        self.db.commit()
        self.db.refresh(knowledge_doc)
        return knowledge_doc

    def list_all(self) -> list[KnowledgeDoc]:
        statement = select(KnowledgeDoc).order_by(KnowledgeDoc.created_at.desc(), KnowledgeDoc.id.desc())
        return list(self.db.scalars(statement).all())

    def get_by_id(self, doc_id: int) -> KnowledgeDoc | None:
        statement = select(KnowledgeDoc).where(KnowledgeDoc.id == doc_id)
        return self.db.scalar(statement)

    def save(self, knowledge_doc: KnowledgeDoc) -> KnowledgeDoc:
        self.db.add(knowledge_doc)
        self.db.commit()
        self.db.refresh(knowledge_doc)
        return knowledge_doc

    def count_chunks(self, doc_id: int) -> int:
        statement = select(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc_id)
        return len(list(self.db.scalars(statement).all()))
