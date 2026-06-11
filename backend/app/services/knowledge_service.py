from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_doc import KnowledgeDoc
from app.models.user import User
from app.repositories.knowledge_chunk_repository import KnowledgeChunkRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import get_embedding_provider
from app.services.vector_store_service import VectorStoreService


ALLOWED_KNOWLEDGE_SUFFIXES = {".txt", ".md"}


@dataclass
class KnowledgeSearchItem:
    doc_id: int
    chunk_id: int
    chunk_index: int
    content_preview: str
    score: float
    embedding_id: str | None


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.chunk_repository = KnowledgeChunkRepository(db)
        self.settings = get_settings()
        self.chunking_service = ChunkingService()
        self.embedding_provider = get_embedding_provider()
        self.vector_store_service = VectorStoreService()

    def upload_document(self, *, file: UploadFile, title: str, current_user: User) -> KnowledgeDoc:
        # 上传阶段只做格式校验、原文保存和 KnowledgeDoc 入库，
        # 真正的 chunk/embedding/index 放到异步处理阶段。
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_KNOWLEDGE_SUFFIXES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .txt and .md files are supported",
            )

        upload_dir = Path(self.settings.knowledge_upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid4().hex}{suffix}"
        file_path = upload_dir / safe_name

        file_bytes = file.file.read()
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be UTF-8 encoded text",
            ) from exc

        file_path.write_bytes(file_bytes)

        knowledge_doc = KnowledgeDoc(
            title=title,
            file_name=file.filename or safe_name,
            file_type=suffix.removeprefix("."),
            file_path=str(file_path.resolve()),
            content=content,
            doc_type="knowledge_base",
            status="uploaded",
            uploaded_by=current_user.id,
            error_message=None,
        )
        return self.repository.create(knowledge_doc)

    def process_document(self, doc_id: int) -> KnowledgeDoc:
        # 后台处理的目标是把文档从 uploaded 推进到 ready，
        # 中间任何失败都要回写状态和错误原因，方便前端展示。
        knowledge_doc = self.get_document(doc_id)
        self._update_document_status(
            knowledge_doc,
            status_value="processing",
            error_message=None,
        )

        try:
            self._create_chunks_for_doc(knowledge_doc)
        except NotImplementedError as exc:
            self._handle_processing_failure(
                knowledge_doc,
                error_message=(
                    "Embedding provider is not available for document processing. "
                    "Set EMBEDDING_PROVIDER=fake for local development."
                ),
            )
            raise
        except OSError as exc:
            self._handle_processing_failure(
                knowledge_doc,
                error_message="Knowledge document processing could not write vector index to disk.",
            )
            raise
        except Exception as exc:
            self._handle_processing_failure(
                knowledge_doc,
                error_message=f"Knowledge document processing failed: {exc}",
            )
            raise

        return self._update_document_status(
            knowledge_doc,
            status_value="ready",
            error_message=None,
        )

    def list_documents(self) -> list[KnowledgeDoc]:
        return self.repository.list_all()

    def get_document(self, doc_id: int) -> KnowledgeDoc:
        knowledge_doc = self.repository.get_by_id(doc_id)
        if knowledge_doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge document not found",
            )
        return knowledge_doc

    def list_chunks(self, doc_id: int) -> list[KnowledgeChunk]:
        self.get_document(doc_id)
        return self.chunk_repository.list_by_doc_id(doc_id)

    def get_chunks_count(self, doc_id: int) -> int:
        return self.repository.count_chunks(doc_id)

    def search_knowledge(self, *, query: str, top_k: int = 5) -> list[KnowledgeSearchItem]:
        # 搜索前会确保 chunk 的 embedding_id 完整，并且按最新 chunk 重建本地索引，
        # 避免文档更新后检索结果仍然落在旧索引上。
        normalized_query = query.strip()
        if not normalized_query:
            return []

        chunks = self.chunk_repository.list_all()
        if not chunks:
            return []

        try:
            self._ensure_chunk_embedding_ids(chunks)
            self.vector_store_service.rebuild_knowledge_index(chunks)
            vector_hits = self.vector_store_service.search_knowledge_chunks(
                query=normalized_query,
                top_k=top_k,
            )
        except NotImplementedError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Embedding provider is not available for knowledge search. "
                    "Set EMBEDDING_PROVIDER=fake for local development."
                ),
            ) from exc
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Knowledge vector index could not be written to disk",
            ) from exc

        chunk_by_id = {chunk.id: chunk for chunk in chunks}
        results: list[KnowledgeSearchItem] = []

        for hit in vector_hits:
            chunk = chunk_by_id.get(hit.chunk_id)
            if chunk is None:
                continue

            results.append(
                KnowledgeSearchItem(
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    content_preview=self._build_content_preview(chunk.content),
                    score=hit.score,
                    embedding_id=chunk.embedding_id,
                )
            )

        return results

    def _create_chunks_for_doc(self, knowledge_doc: KnowledgeDoc) -> list[KnowledgeChunk]:
        # 每次重处理文档都先删旧 chunk，再按当前配置重新切分并重建索引，
        # 保证数据库和本地向量文件是一致的。
        self.chunk_repository.delete_by_doc_id(knowledge_doc.id)
        chunk_texts = self.chunking_service.split_text(knowledge_doc.content)
        chunks = [
            KnowledgeChunk(
                doc_id=knowledge_doc.id,
                chunk_index=index,
                content=chunk_text,
                metadata_json={
                    "chunk_size": self.chunking_service.config.chunk_size,
                    "overlap": self.chunking_service.config.overlap,
                    "embedding_provider": self.settings.embedding_provider,
                    "embedding_dimension": self.settings.embedding_dimension,
                },
                embedding_id=self.embedding_provider.build_embedding_id(chunk_text),
            )
            for index, chunk_text in enumerate(chunk_texts)
        ]
        if not chunks:
            self._rebuild_knowledge_index()
            return []
        created_chunks = self.chunk_repository.create_many(chunks)
        self._rebuild_knowledge_index()
        return created_chunks

    def _ensure_chunk_embedding_ids(self, chunks: list[KnowledgeChunk]) -> None:
        for chunk in chunks:
            if chunk.embedding_id:
                continue
            chunk.embedding_id = self.embedding_provider.build_embedding_id(chunk.content)
            self.chunk_repository.save(chunk)

    @staticmethod
    def _build_content_preview(content: str, max_length: int = 200) -> str:
        normalized = " ".join(content.split()).strip()
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[: max_length - 3]}..."

    def _update_document_status(
        self,
        knowledge_doc: KnowledgeDoc,
        *,
        status_value: str,
        error_message: str | None,
    ) -> KnowledgeDoc:
        knowledge_doc.status = status_value
        knowledge_doc.error_message = error_message
        return self.repository.save(knowledge_doc)

    def _handle_processing_failure(self, knowledge_doc: KnowledgeDoc, *, error_message: str) -> None:
        self.chunk_repository.delete_by_doc_id(knowledge_doc.id)
        try:
            self._rebuild_knowledge_index()
        except OSError:
            pass
        self._update_document_status(
            knowledge_doc,
            status_value="failed",
            error_message=error_message,
        )

    def _rebuild_knowledge_index(self) -> None:
        self.vector_store_service.rebuild_knowledge_index(self.chunk_repository.list_all())


def process_knowledge_document_task(doc_id: int) -> None:
    db = SessionLocal()
    try:
        KnowledgeService(db).process_document(doc_id)
    finally:
        db.close()
