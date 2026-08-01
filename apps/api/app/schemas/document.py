from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    filename: str
    original_filename: str
    mime_type: str
    status: str
    page_count: Optional[int]
    chunk_count: int = 0
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
