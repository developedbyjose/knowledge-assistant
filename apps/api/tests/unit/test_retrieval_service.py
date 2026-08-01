from uuid import uuid4

from app.rag.retrieval.types import RetrievedChunk
from app.services.retrieval_service import RetrievalService


class FakeKnowledgeBases:
    def get(self, knowledge_base_id):  # noqa: ANN001
        return object()


class FakeDocuments:
    def search_chunks(self, *, knowledge_base_id, embedding, limit):  # noqa: ANN001
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
            )
            for index in range(1, limit + 1)
        ]


class FakeEmbeddingProvider:
    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 384


def test_retrieval_returns_top_five_in_order() -> None:
    service = RetrievalService(session=None, embedding_provider=FakeEmbeddingProvider())  # type: ignore[arg-type]
    service.knowledge_bases = FakeKnowledgeBases()
    service.documents = FakeDocuments()

    results = service.retrieve(knowledge_base_id=uuid4(), question="What changed?", limit=5)

    assert len(results.results) == 5
    assert [result.rank for result in results.results] == [1, 2, 3, 4, 5]
