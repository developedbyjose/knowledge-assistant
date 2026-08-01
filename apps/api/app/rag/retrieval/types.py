from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    filename: str
    rank: int
    similarity_score: float
    content: str
    page_number: int | None
    chunk_index: int
