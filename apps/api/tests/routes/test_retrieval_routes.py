from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1.dependencies import (
    get_document_service,
    get_knowledge_base_service,
    get_retrieval_service,
)
from app.main import app
from app.schemas.document import DocumentRead
from app.schemas.knowledge_base import KnowledgeBaseRead
from app.schemas.retrieval import DocumentUploadRead, RetrievalResults

MISSING_ID = UUID("00000000-0000-0000-0000-000000000404")
PROCESSED_ID = UUID("00000000-0000-0000-0000-000000000101")
FAILED_ID = UUID("00000000-0000-0000-0000-000000000202")


class FakeKnowledgeBaseService:
    def list(self):  # noqa: ANN201
        return []

    def get(self, knowledge_base_id):  # noqa: ANN001, ANN201
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")
        return self._read(id=knowledge_base_id, name="Retrieval Lab", description="Test")

    def create(self, *, name, description):  # noqa: ANN001, ANN201
        return self._read(id=uuid4(), name=name, description=description)

    def update(self, *, knowledge_base_id, values):  # noqa: ANN001, ANN201
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")
        return self._read(
            id=knowledge_base_id,
            name=values.get("name", "Retrieval Lab"),
            description=values.get("description", "Test"),
        )

    def delete(self, knowledge_base_id):  # noqa: ANN001, ANN201
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")

    def _read(self, *, id, name, description):  # noqa: ANN001, A002, ANN201
        return KnowledgeBaseRead(
            id=id,
            name=name,
            description=description,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            created_at="2026-08-01T00:00:00Z",
            document_count=1,
            chunk_count=2,
        )


class FakeDocumentService:
    async def upload_pdf(self, *, knowledge_base_id, upload):  # noqa: ANN001, ANN201
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")

        content = await upload.read()
        if upload.content_type != "application/pdf":
            raise ValueError("Only PDF uploads are supported.")
        if not (upload.filename or "").lower().endswith(".pdf"):
            raise ValueError("Only PDF uploads are supported.")
        if not content:
            raise ValueError("Uploaded PDF cannot be empty.")
        if len(content) > 26_214_400:
            raise ValueError("Uploaded PDF must be 25 MB or smaller.")
        if not content.startswith(b"%PDF-"):
            raise ValueError("Uploaded file does not appear to be a valid PDF.")

        return DocumentUploadRead(
            id=uuid4(),
            filename="sample.pdf",
            original_filename=upload.filename,
            status="processed",
            page_count=1,
            chunk_count=2,
            error_message=None,
        )

    def list_by_knowledge_base(self, knowledge_base_id):  # noqa: ANN001, ANN201
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")
        return [self._read()]

    def get(self, document_id):  # noqa: ANN001, ANN201
        if document_id == MISSING_ID:
            raise LookupError("Document not found.")
        return self._read(id=document_id)

    def delete(self, document_id):  # noqa: ANN001, ANN201
        if document_id == MISSING_ID:
            raise LookupError("Document not found.")

    def reprocess(self, document_id):  # noqa: ANN001, ANN201
        if document_id == MISSING_ID:
            raise LookupError("Document not found.")
        if document_id == FAILED_ID:
            return self._read(
                id=document_id,
                status="failed",
                chunk_count=0,
                error_message="Stored document file not found.",
            )
        return self._read(id=document_id, status="processed", chunk_count=2)

    def _read(  # noqa: ANN201
        self,
        *,
        id=None,  # noqa: A002, ANN001
        status="processed",  # noqa: ANN001
        chunk_count=2,  # noqa: ANN001
        error_message=None,  # noqa: ANN001
    ):
        return DocumentRead(
            id=id or uuid4(),
            knowledge_base_id=uuid4(),
            filename="sample.pdf",
            original_filename="sample.pdf",
            mime_type="application/pdf",
            status=status,
            page_count=1 if status == "processed" else None,
            chunk_count=chunk_count,
            error_message=error_message,
            created_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
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


def test_rejects_empty_pdf_upload() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/documents",
        files={"file": ("sample.pdf", b"", "application/pdf")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded PDF cannot be empty."


def test_rejects_oversized_pdf_upload() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/documents",
        files={"file": ("sample.pdf", b"%PDF-" + (b"0" * 26_214_401), "application/pdf")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded PDF must be 25 MB or smaller."


def test_rejects_invalid_pdf_signature() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/documents",
        files={"file": ("sample.pdf", b"not a pdf", "application/pdf")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file does not appear to be a valid PDF."


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


def test_upload_missing_knowledge_base_returns_404() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{MISSING_ID}/documents",
        files={"file": ("sample.pdf", b"%PDF-1.4", "application/pdf")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


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


def test_get_knowledge_base_route() -> None:
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBaseService()
    client = TestClient(app)
    knowledge_base_id = uuid4()

    response = client.get(f"/api/v1/knowledge-bases/{knowledge_base_id}")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["id"] == str(knowledge_base_id)
    assert response.json()["document_count"] == 1


def test_update_knowledge_base_route() -> None:
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBaseService()
    client = TestClient(app)

    response = client.patch(
        f"/api/v1/knowledge-bases/{uuid4()}",
        json={"name": "Updated", "description": None},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    assert response.json()["description"] is None


def test_rejects_empty_knowledge_base_update() -> None:
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBaseService()
    client = TestClient(app)

    response = client.patch(f"/api/v1/knowledge-bases/{uuid4()}", json={})

    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_delete_knowledge_base_route() -> None:
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBaseService()
    client = TestClient(app)

    response = client.delete(f"/api/v1/knowledge-bases/{uuid4()}")

    app.dependency_overrides.clear()
    assert response.status_code == 204
    assert response.content == b""


def test_missing_knowledge_base_returns_404() -> None:
    app.dependency_overrides[get_knowledge_base_service] = lambda: FakeKnowledgeBaseService()
    client = TestClient(app)

    response = client.get(f"/api/v1/knowledge-bases/{MISSING_ID}")

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_list_documents_route() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.get(f"/api/v1/knowledge-bases/{uuid4()}/documents")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["chunk_count"] == 2


def test_get_document_route() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)
    document_id = uuid4()

    response = client.get(f"/api/v1/documents/{document_id}")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["id"] == str(document_id)


def test_delete_document_route() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.delete(f"/api/v1/documents/{uuid4()}")

    app.dependency_overrides.clear()
    assert response.status_code == 204
    assert response.content == b""


def test_reprocess_document_route() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(f"/api/v1/documents/{PROCESSED_ID}/reprocess")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_reprocess_document_can_return_failed_status() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.post(f"/api/v1/documents/{FAILED_ID}/reprocess")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == "Stored document file not found."


def test_missing_document_returns_404() -> None:
    app.dependency_overrides[get_document_service] = lambda: FakeDocumentService()
    client = TestClient(app)

    response = client.get(f"/api/v1/documents/{MISSING_ID}")

    app.dependency_overrides.clear()
    assert response.status_code == 404
