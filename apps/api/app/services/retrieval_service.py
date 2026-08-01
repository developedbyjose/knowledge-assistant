from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag.providers.embedding import EmbeddingProvider
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.retrieval import RetrievalResult, RetrievalResults


class RetrievalService:
    def __init__(
        self,
        *,
        session: Session,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session = session
        self.embedding_provider = embedding_provider
        self.documents = DocumentRepository(session)
        self.knowledge_bases = KnowledgeBaseRepository(session)

    def retrieve(
        self,
        *,
        knowledge_base_id: UUID,
        question: str,
        limit: int = 5,
    ) -> RetrievalResults:
        knowledge_base = self.knowledge_bases.get(knowledge_base_id)
        if knowledge_base is None:
            raise LookupError("Knowledge base not found.")
        if knowledge_base.embedding_model != settings.embedding_model:
            raise ValueError(
                "Knowledge base embedding model does not match the configured embedding model."
            )

        query_embedding = self.embedding_provider.embed_query(question)
        if len(query_embedding) != settings.embedding_dimensions:
            raise ValueError("Query embedding dimensions do not match the configured vector size.")

        chunks = self.documents.search_chunks(
            knowledge_base_id=knowledge_base_id,
            embedding=query_embedding,
            limit=limit,
        )
        return RetrievalResults(
            question=question,
            results=[
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    rank=chunk.rank,
                    similarity_score=chunk.similarity_score,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    metadata=chunk.metadata,
                )
                for chunk in chunks
            ],
        )
