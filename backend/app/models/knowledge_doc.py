from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class KnowledgeDoc(TimestampMixin, Base):
    __tablename__ = "knowledge_docs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, default="knowledge_base")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ready")
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
