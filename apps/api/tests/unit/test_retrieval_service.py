from uuid import uuid4

import pytest

from app.core.config import settings
from app.rag.retrieval.types import RetrievedChunk
from app.services.retrieval_service import RetrievalService


class FakeKnowledgeBases:
    def __init__(self, *, embedding_model=None, missing=False):  # noqa: ANN001
        self.embedding_model = embedding_model or settings.embedding_model
        self.missing = missing

    def get(self, knowledge_base_id):  # noqa: ANN001
        if self.missing:
            return None

        return type("KnowledgeBase", (), {"embedding_model": self.embedding_model})()


class FakeDocuments:
    def __init__(self) -> None:
        self.limit = None
        self.embedding = None

    def search_chunks(self, *, knowledge_base_id, embedding, limit):  # noqa: ANN001
        self.limit = limit
        self.embedding = embedding
        return [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                filename=f"doc-{index}.pdf",
                rank=index,
                similarity_score=1.0 - index / 10,
                content=f"content {index}",
                page_number=index,
                chunk_index=index,
                metadata={"page_number": index},
            )
            for index in range(1, limit + 1)
        ]


class FakeEmbeddingProvider:
    def __init__(self, *, dimensions=384) -> None:  # noqa: ANN001
        self.dimensions = dimensions
        self.queries: list[str] = []

    def embed_query(self, text: str) -> list[float]:
        self.queries.append(text)
        return [0.1] * self.dimensions


def test_retrieval_returns_top_five_in_order() -> None:
    provider = FakeEmbeddingProvider()
    documents = FakeDocuments()
    service = RetrievalService(session=None, embedding_provider=provider)  # type: ignore[arg-type]
    service.knowledge_bases = FakeKnowledgeBases()
    service.documents = documents

    results = service.retrieve(knowledge_base_id=uuid4(), question="What changed?", limit=5)

    assert len(results.results) == 5
    assert [result.rank for result in results.results] == [1, 2, 3, 4, 5]
    assert provider.queries == ["What changed?"]
    assert documents.limit == 5
    assert documents.embedding == [0.1] * settings.embedding_dimensions
    assert results.results[0].metadata == {"page_number": 1}


def test_retrieval_missing_knowledge_base_raises_lookup_error() -> None:
    service = RetrievalService(session=None, embedding_provider=FakeEmbeddingProvider())  # type: ignore[arg-type]
    service.knowledge_bases = FakeKnowledgeBases(missing=True)
    service.documents = FakeDocuments()

    with pytest.raises(LookupError, match="Knowledge base not found"):
        service.retrieve(knowledge_base_id=uuid4(), question="What changed?", limit=5)


def test_retrieval_rejects_embedding_model_mismatch() -> None:
    provider = FakeEmbeddingProvider()
    service = RetrievalService(session=None, embedding_provider=provider)  # type: ignore[arg-type]
    service.knowledge_bases = FakeKnowledgeBases(embedding_model="other-model")
    service.documents = FakeDocuments()

    with pytest.raises(ValueError, match="embedding model"):
        service.retrieve(knowledge_base_id=uuid4(), question="What changed?", limit=5)

    assert provider.queries == []


def test_retrieval_rejects_embedding_dimension_mismatch() -> None:
    service = RetrievalService(
        session=None,
        embedding_provider=FakeEmbeddingProvider(dimensions=settings.embedding_dimensions + 1),
    )  # type: ignore[arg-type]
    service.knowledge_bases = FakeKnowledgeBases()
    service.documents = FakeDocuments()

    with pytest.raises(ValueError, match="dimensions"):
        service.retrieve(knowledge_base_id=uuid4(), question="What changed?", limit=5)
