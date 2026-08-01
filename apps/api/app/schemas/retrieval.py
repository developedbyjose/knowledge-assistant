from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadRead(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    status: str
    page_count: Optional[int]
    chunk_count: int
    error_message: Optional[str]


class RetrievalQuery(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class RetrievalResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str
    rank: int
    similarity_score: float
    content: str
    page_number: Optional[int]
    chunk_index: int


class RetrievalResults(BaseModel):
    question: str
    results: list[RetrievalResult]
