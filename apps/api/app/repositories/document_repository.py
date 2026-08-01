from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.rag.ingestion.chunker import Chunk
from app.rag.retrieval.types import RetrievedChunk


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_pending(
        self,
        *,
        knowledge_base_id: UUID,
        filename: str,
        original_filename: str,
        mime_type: str,
        storage_key: str,
    ) -> Document:
        document = Document(
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            original_filename=original_filename,
            mime_type=mime_type,
            storage_key=storage_key,
            status="pending",
        )
        self.session.add(document)
        self.session.flush()
        return document

    def mark_processing(self, document: Document) -> None:
        document.status = "processing"
        document.error_message = None
        self.session.flush()

    def mark_processed(self, document: Document, *, page_count: int) -> None:
        document.status = "processed"
        document.page_count = page_count
        document.error_message = None
        document.processed_at = datetime.now(timezone.utc)
        self.session.flush()

    def mark_failed(self, document: Document, *, error_message: str) -> None:
        document.status = "failed"
        document.error_message = error_message
        document.processed_at = datetime.now(timezone.utc)
        self.session.flush()

    def add_chunks(
        self,
        *,
        document: Document,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> list[DocumentChunk]:
        rows = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                section_title=None,
                token_count=chunk.token_count,
                chunk_metadata=chunk.metadata,
                embedding=embedding,
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]
        self.session.add_all(rows)
        self.session.flush()
        return rows

    def search_chunks(
        self,
        *,
        knowledge_base_id: UUID,
        embedding: list[float],
        limit: int,
    ) -> list[RetrievedChunk]:
        distance = DocumentChunk.embedding.cosine_distance(embedding).label("distance")
        statement = (
            select(DocumentChunk, Document, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.knowledge_base_id == knowledge_base_id)
            .order_by(distance.asc())
            .limit(limit)
        )

        results: list[RetrievedChunk] = []
        for rank, (chunk, document, raw_distance) in enumerate(self.session.execute(statement), start=1):
            distance_value = float(raw_distance)
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    filename=document.original_filename,
                    rank=rank,
                    similarity_score=max(0.0, 1.0 - distance_value),
                    content=chunk.content,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                )
            )
        return results
