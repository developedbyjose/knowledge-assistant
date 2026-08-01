from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge_base import KnowledgeBaseRead


class KnowledgeBaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[KnowledgeBaseRead]:
        statement = (
            select(
                KnowledgeBase,
                func.count(func.distinct(Document.id)).label("document_count"),
                func.count(DocumentChunk.id).label("chunk_count"),
            )
            .outerjoin(Document, Document.knowledge_base_id == KnowledgeBase.id)
            .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
            .group_by(KnowledgeBase.id)
            .order_by(KnowledgeBase.created_at.desc())
        )

        return [
            KnowledgeBaseRead.model_validate(
                knowledge_base,
                from_attributes=True,
            ).model_copy(
                update={
                    "document_count": document_count,
                    "chunk_count": chunk_count,
                }
            )
            for knowledge_base, document_count, chunk_count in self.session.execute(statement)
        ]

    def get(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        return self.session.get(KnowledgeBase, knowledge_base_id)

    def create(
        self,
        *,
        name: str,
        description: str | None,
        embedding_model: str,
    ) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(
            name=name,
            description=description,
            embedding_model=embedding_model,
        )
        self.session.add(knowledge_base)
        self.session.flush()
        return knowledge_base
