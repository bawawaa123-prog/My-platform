from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeChunkRead,
    KnowledgeDocRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
)
from app.services.knowledge_service import KnowledgeService, process_knowledge_document_task


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def build_knowledge_doc_response(
    knowledge_doc,
    *,
    chunks_count: int,
) -> KnowledgeDocRead:
    response = KnowledgeDocRead.model_validate(knowledge_doc)
    return response.model_copy(update={"chunks_count": chunks_count})


@router.post("/upload", response_model=KnowledgeDocRead)
def upload_knowledge_doc(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocRead:
    # 上传接口只负责“快速落库 + 投递后台任务”，
    # 切分、embedding、索引都交给后台处理，避免阻塞前端。
    service = KnowledgeService(db)
    knowledge_doc = service.upload_document(
        file=file,
        title=title,
        current_user=current_user,
    )
    background_tasks.add_task(process_knowledge_document_task, knowledge_doc.id)
    return build_knowledge_doc_response(
        knowledge_doc,
        chunks_count=service.get_chunks_count(knowledge_doc.id),
    )


@router.get("/docs", response_model=list[KnowledgeDocRead])
def list_knowledge_docs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeDocRead]:
    service = KnowledgeService(db)
    docs = service.list_documents()
    return [
        build_knowledge_doc_response(
            doc,
            chunks_count=service.get_chunks_count(doc.id),
        )
        for doc in docs
    ]


@router.get("/docs/{doc_id}", response_model=KnowledgeDocRead)
def get_knowledge_doc(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocRead:
    service = KnowledgeService(db)
    knowledge_doc = service.get_document(doc_id)
    return build_knowledge_doc_response(
        knowledge_doc,
        chunks_count=service.get_chunks_count(knowledge_doc.id),
    )


@router.get("/docs/{doc_id}/chunks", response_model=list[KnowledgeChunkRead])
def list_knowledge_chunks(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeChunkRead]:
    chunks = KnowledgeService(db).list_chunks(doc_id)
    return [KnowledgeChunkRead.model_validate(chunk) for chunk in chunks]


@router.post("/search", response_model=list[KnowledgeSearchResult])
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeSearchResult]:
    # 统一通过 KnowledgeService 做语义检索，API 层不直接碰向量索引细节。
    results = KnowledgeService(db).search_knowledge(
        query=payload.query,
        top_k=payload.top_k,
    )
    return [KnowledgeSearchResult.model_validate(result) for result in results]
