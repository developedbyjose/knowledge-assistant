from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from app.repositories.document_repository import DocumentRepository


@pytest.mark.skipif(
    os.environ.get("RUN_PGVECTOR_TESTS") != "1",
    reason="Set RUN_PGVECTOR_TESTS=1 with a pgvector database to run repository vector tests.",
)
def test_search_chunks_ranks_processed_documents_by_cosine_distance() -> None:
    engine = create_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.drop_all(connection)
        Base.metadata.create_all(connection)

    with Session(engine) as session:
        knowledge_base = KnowledgeBase(
            id=uuid4(),
            name="Vector Test",
            description=None,
            embedding_model=settings.embedding_model,
        )
        processed = Document(
            knowledge_base_id=knowledge_base.id,
            filename="processed.pdf",
            original_filename="processed.pdf",
            mime_type="application/pdf",
            storage_key="processed.pdf",
            status="processed",
        )
        failed = Document(
            knowledge_base_id=knowledge_base.id,
            filename="failed.pdf",
            original_filename="failed.pdf",
            mime_type="application/pdf",
            storage_key="failed.pdf",
            status="failed",
        )
        session.add_all([knowledge_base, processed, failed])
        session.flush()

        session.add_all(
            [
                DocumentChunk(
                    document_id=processed.id,
                    chunk_index=0,
                    content="best policy chunk",
                    page_number=1,
                    token_count=3,
                    chunk_metadata={"kind": "best"},
                    embedding=_embedding(1.0, 0.0),
                ),
                DocumentChunk(
                    document_id=processed.id,
                    chunk_index=1,
                    content="second policy chunk",
                    page_number=1,
                    token_count=3,
                    chunk_metadata={"kind": "second"},
                    embedding=_embedding(0.7, 0.7),
                ),
                DocumentChunk(
                    document_id=failed.id,
                    chunk_index=0,
                    content="failed document should not rank",
                    page_number=1,
                    token_count=5,
                    chunk_metadata={"kind": "failed"},
                    embedding=_embedding(1.0, 0.0),
                ),
            ]
        )
        session.commit()

        results = DocumentRepository(session).search_chunks(
            knowledge_base_id=knowledge_base.id,
            embedding=_embedding(1.0, 0.0),
            limit=5,
        )

    assert [result.content for result in results] == ["best policy chunk", "second policy chunk"]
    assert results[0].metadata == {"kind": "best"}


def _embedding(first: float, second: float) -> list[float]:
    return [first, second, *([0.0] * (settings.embedding_dimensions - 2))]
