from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.dependencies import (
    get_document_service,
    get_knowledge_base_service,
    get_retrieval_service,
)
from app.main import app
from app.schemas.knowledge_base import KnowledgeBaseRead
from app.schemas.retrieval import DocumentUploadRead, RetrievalResults


class FakeKnowledgeBaseService:
    def list(self):  # noqa: ANN201
        return []

    def create(self, *, name, description):  # noqa: ANN001, ANN201
        return KnowledgeBaseRead(
            id=uuid4(),
            name=name,
            description=description,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            created_at="2026-08-01T00:00:00Z",
        )


class FakeDocumentService:
    async def upload_pdf(self, *, knowledge_base_id, upload):  # noqa: ANN001, ANN201
        if upload.content_type != "application/pdf":
            raise ValueError("Only PDF uploads are supported.")

        return DocumentUploadRead(
            id=uuid4(),
            filename="sample.pdf",
            original_filename=upload.filename,
            status="processed",
            page_count=1,
            chunk_count=2,
            error_message=None,
        )


class FakeRetrievalService:
    def retrieve(self, *, knowledge_base_id, question, limit):  # noqa: ANN001, ANN201
        return RetrievalResults(question=question, results=[])


def test_rejects_non_pdf_upload() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/documents",
        files={"file": ("sample.txt", b"hello", "text/plain")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_upload_pdf_returns_document_status() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/documents",
        files={"file": ("sample.pdf", b"%PDF-1.4", "application/pdf")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_query_before_chunks_returns_empty_results() -> None:
    app.dependency_overrides[get_retrieval_service] = lambda: FakeRetrievalService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/retrieval-query",
        json={"question": "What is this about?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_create_knowledge_base_route() -> None:
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBaseService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/knowledge-bases",
        json={"name": "Retrieval Lab", "description": "Test"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["name"] == "Retrieval Lab"
