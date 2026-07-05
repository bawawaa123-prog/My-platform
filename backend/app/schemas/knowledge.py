from pydantic import BaseModel, ConfigDict, Field

from app.utils.datetime_utils import UTCDatetime


class KnowledgeChunkRead(BaseModel):
    id: int
    doc_id: int
    chunk_index: int
    content: str
    metadata_json: dict
    embedding_id: str | None
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocRead(BaseModel):
    id: int
    title: str
    file_name: str
    file_type: str
    file_path: str
    content: str
    doc_type: str
    status: str
    uploaded_by: int
    error_message: str | None
    chunks_count: int = 0
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResult(BaseModel):
    doc_id: int
    chunk_id: int
    chunk_index: int
    content_preview: str
    score: float
    embedding_id: str | None

    model_config = ConfigDict(from_attributes=True)
