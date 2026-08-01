from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.knowledge_base import KnowledgeBaseRead


class KnowledgeBaseService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.knowledge_bases = KnowledgeBaseRepository(session)

    def list(self) -> list[KnowledgeBaseRead]:
        return self.knowledge_bases.list()

    def get(self, knowledge_base_id: UUID) -> KnowledgeBaseRead:
        knowledge_base = self.knowledge_bases.get_with_counts(knowledge_base_id)
        if knowledge_base is None:
            raise LookupError("Knowledge base not found.")
        return knowledge_base

    def create(self, *, name: str, description: str | None) -> KnowledgeBase:
        knowledge_base = self.knowledge_bases.create(
            name=name,
            description=description,
            embedding_model=settings.embedding_model,
        )
        self.session.commit()
        self.session.refresh(knowledge_base)
        return knowledge_base

    def update(
        self,
        *,
        knowledge_base_id: UUID,
        values: dict[str, str | None],
    ) -> KnowledgeBaseRead:
        knowledge_base = self.get_required(knowledge_base_id)
        self.knowledge_bases.update(
            knowledge_base,
            values=values,
        )
        self.session.commit()
        return self.get(knowledge_base_id)

    def delete(self, knowledge_base_id: UUID) -> None:
        knowledge_base = self.get_required(knowledge_base_id)
        stored_paths = [
            Path(settings.upload_dir) / document.storage_key
            for document in knowledge_base.documents
        ]
        self.knowledge_bases.delete(knowledge_base)
        self.session.commit()
        for stored_path in stored_paths:
            if stored_path.exists():
                stored_path.unlink()

    def get_or_create_default(self) -> KnowledgeBase:
        existing = self.knowledge_bases.list()
        if existing:
            return self.get_required(existing[0].id)

        return self.create(
            name="Retrieval Lab",
            description="Default knowledge base for retrieval validation.",
        )

    def get_required(self, knowledge_base_id: UUID) -> KnowledgeBase:
        knowledge_base = self.knowledge_bases.get(knowledge_base_id)
        if knowledge_base is None:
            raise LookupError("Knowledge base not found.")
        return knowledge_base
