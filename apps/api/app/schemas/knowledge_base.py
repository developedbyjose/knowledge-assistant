from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    embedding_model: str
    created_at: datetime
    document_count: int = 0
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)


def default_knowledge_base_create() -> KnowledgeBaseCreate:
    return KnowledgeBaseCreate(
        name="Retrieval Lab",
        description=f"Default workspace for {settings.embedding_model} retrieval validation.",
    )
