from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1.dependencies import (
    get_conversation_service,
    get_document_service,
    get_answer_service,
    get_knowledge_base_service,
    get_retrieval_service,
)
from app.main import app
from app.rag.providers.chat import ChatModelError
from app.schemas.conversation import ConversationMessageResponse, ConversationRead, MessageFeedbackRead, MessageRead
from app.schemas.document import DocumentRead
from app.schemas.knowledge_base import KnowledgeBaseRead
from app.schemas.retrieval import AnswerCitation, CitedAnswer, DocumentUploadRead, RetrievalResult, RetrievalResults

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
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")

        return RetrievalResults(
            question=question,
            results=[
                RetrievalResult(
                    chunk_id=uuid4(),
                    document_id=uuid4(),
                    filename="retrieval-baseline.pdf",
                    rank=1,
                    similarity_score=0.92,
                    content="Query embeddings rank policy chunks above onboarding chunks.",
                    page_number=1,
                    chunk_index=0,
                    metadata={"source": "pdf", "page_number": 1},
                )
            ],
        )


class FakeAnswerService:
    def __init__(self, *, error=None):  # noqa: ANN001
        self.error = error

    async def answer(self, *, knowledge_base_id, question, limit):  # noqa: ANN001, ANN201
        if self.error:
            raise self.error
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")

        chunk_id = uuid4()
        document_id = uuid4()
        return CitedAnswer(
            question=question,
            answer="Query embeddings rank policy chunks above onboarding chunks [1].",
            citations=[
                AnswerCitation(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename="retrieval-baseline.pdf",
                    page_number=1,
                    chunk_index=0,
                    rank=1,
                )
            ],
            source_chunks=[
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename="retrieval-baseline.pdf",
                    rank=1,
                    similarity_score=0.92,
                    content="Query embeddings rank policy chunks above onboarding chunks.",
                    page_number=1,
                    chunk_index=0,
                    metadata={"source": "pdf", "page_number": 1},
                )
            ],
        )


class FakeConversationService:
    def __init__(self, *, error=None):  # noqa: ANN001
        self.error = error
        self.conversation_id = uuid4()
        self.knowledge_base_id = uuid4()
        self.user_message_id = uuid4()
        self.assistant_message_id = uuid4()

    def create(self, *, knowledge_base_id, title):  # noqa: ANN001, ANN201
        if self.error:
            raise self.error
        if knowledge_base_id == MISSING_ID:
            raise LookupError("Knowledge base not found.")
        return self._conversation(knowledge_base_id=knowledge_base_id, title=title or "New chat")

    def list(self):  # noqa: ANN201
        return [self._conversation()]

    def get(self, conversation_id):  # noqa: ANN001, ANN201
        if conversation_id == MISSING_ID:
            raise LookupError("Conversation not found.")
        return self._conversation(
            id=conversation_id,
            messages=[
                self._message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content="Grounded answer [1].",
                    model_name="gemini-flash-lite-latest",
                    with_sources=True,
                )
            ],
        )

    def delete(self, conversation_id):  # noqa: ANN001, ANN201
        if conversation_id == MISSING_ID:
            raise LookupError("Conversation not found.")

    async def add_message(self, *, conversation_id, content, limit):  # noqa: ANN001, ANN201
        if self.error:
            raise self.error
        if conversation_id == MISSING_ID:
            raise LookupError("Conversation not found.")
        user_message = self._message(conversation_id=conversation_id, role="user", content=content)
        assistant_message = self._message(
            conversation_id=conversation_id,
            role="assistant",
            content="Grounded answer [1].",
            model_name="gemini-flash-lite-latest",
            with_sources=True,
        )
        chunk_id = uuid4()
        document_id = uuid4()
        return ConversationMessageResponse(
            conversation=self._conversation(id=conversation_id, messages=[user_message, assistant_message]),
            user_message=user_message,
            assistant_message=assistant_message,
            citations=[
                AnswerCitation(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename="policy.pdf",
                    page_number=1,
                    chunk_index=0,
                    rank=1,
                )
            ],
            source_chunks=[
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename="policy.pdf",
                    rank=1,
                    similarity_score=0.9,
                    content="Policy evidence.",
                    page_number=1,
                    chunk_index=0,
                    metadata={"page_number": 1},
                )
            ],
        )

    async def stream_message(self, *, conversation_id, content, limit):  # noqa: ANN001, ANN201
        user_message = self._message(conversation_id=conversation_id, role="user", content=content)
        assistant_message = self._message(
            conversation_id=conversation_id,
            role="assistant",
            content="Grounded answer [1].",
            model_name="gemini-flash-lite-latest",
            with_sources=True,
        )
        yield {
            "event": "message_start",
            "data": {
                "conversation_id": str(conversation_id),
                "user_message": user_message.model_dump(mode="json"),
            },
        }
        yield {"event": "token", "data": {"content": "Grounded answer [1]."}}
        yield {"event": "sources", "data": {"citations": [], "source_chunks": []}}
        yield {
            "event": "message_done",
            "data": {
                "conversation": self._conversation(
                    id=conversation_id,
                    messages=[user_message, assistant_message],
                ).model_dump(mode="json"),
                "assistant_message": assistant_message.model_dump(mode="json"),
            },
        }

    def record_feedback(self, *, message_id, rating):  # noqa: ANN001, ANN201
        if message_id == MISSING_ID:
            raise LookupError("Message not found.")
        if message_id == UUID("00000000-0000-0000-0000-000000000400"):
            raise ValueError("Feedback can only be recorded for assistant messages.")
        return MessageFeedbackRead(
            id=uuid4(),
            message_id=message_id,
            rating=rating,
            created_at=datetime.now(timezone.utc),
        )

    def _conversation(self, *, id=None, knowledge_base_id=None, title="New chat", messages=None):  # noqa: A002, ANN001, ANN201
        return ConversationRead(
            id=id or self.conversation_id,
            user_id=None,
            knowledge_base_id=knowledge_base_id or self.knowledge_base_id,
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            messages=messages or [],
        )

    def _message(self, *, conversation_id, role, content, model_name=None, with_sources=False):  # noqa: ANN001, ANN201
        chunk_id = uuid4()
        document_id = uuid4()
        return MessageRead(
            id=uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_name=model_name,
            created_at=datetime.now(timezone.utc),
            citations=[
                AnswerCitation(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename="policy.pdf",
                    page_number=1,
                    chunk_index=0,
                    rank=1,
                    similarity_score=0.9,
                )
            ]
            if with_sources
            else [],
            source_chunks=[
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename="policy.pdf",
                    rank=1,
                    similarity_score=0.9,
                    content="Policy evidence.",
                    page_number=1,
                    chunk_index=0,
                    metadata={"page_number": 1},
                )
            ]
            if with_sources
            else [],
        )


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


def test_query_embedding_returns_ranked_chunks() -> None:
    app.dependency_overrides[get_retrieval_service] = lambda: FakeRetrievalService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/query-embedding",
        json={"question": "What is this about?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["rank"] == 1
    assert body["results"][0]["metadata"] == {"source": "pdf", "page_number": 1}


def test_retrieval_query_alias_still_returns_chunks() -> None:
    app.dependency_overrides[get_retrieval_service] = lambda: FakeRetrievalService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/retrieval-query",
        json={"question": "What is this about?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["results"][0]["filename"] == "retrieval-baseline.pdf"


def test_query_embedding_validates_payload() -> None:
    app.dependency_overrides[get_retrieval_service] = lambda: FakeRetrievalService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/query-embedding",
        json={"question": "", "limit": 21},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_query_embedding_missing_knowledge_base_returns_404() -> None:
    app.dependency_overrides[get_retrieval_service] = lambda: FakeRetrievalService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{MISSING_ID}/query-embedding",
        json={"question": "What is this about?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_answer_question_returns_cited_answer() -> None:
    app.dependency_overrides[get_answer_service] = lambda: FakeAnswerService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/answers",
        json={"question": "How are chunks ranked?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "How are chunks ranked?"
    assert body["answer"].endswith("[1].")
    assert body["citations"][0]["filename"] == "retrieval-baseline.pdf"
    assert body["citations"][0]["rank"] == 1
    assert body["source_chunks"][0]["metadata"] == {"source": "pdf", "page_number": 1}


def test_answer_question_validates_payload() -> None:
    app.dependency_overrides[get_answer_service] = lambda: FakeAnswerService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/answers",
        json={"question": "", "limit": 21},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_answer_question_missing_knowledge_base_returns_404() -> None:
    app.dependency_overrides[get_answer_service] = lambda: FakeAnswerService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{MISSING_ID}/answers",
        json={"question": "How are chunks ranked?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_answer_question_retrieval_config_error_returns_400() -> None:
    app.dependency_overrides[get_answer_service] = lambda: FakeAnswerService(
        error=ValueError("Knowledge base embedding model does not match the configured embedding model.")
    )
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/answers",
        json={"question": "How are chunks ranked?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_answer_question_provider_error_returns_502() -> None:
    app.dependency_overrides[get_answer_service] = lambda: FakeAnswerService(
        error=ChatModelError("Gemini API key is not configured.")
    )
    client = TestClient(app)

    response = client.post(
        f"/api/v1/knowledge-bases/{uuid4()}/answers",
        json={"question": "How are chunks ranked?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 502
    assert response.json()["detail"] == "Gemini API key is not configured."


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


def test_create_conversation_route() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)
    knowledge_base_id = uuid4()

    response = client.post(
        "/api/v1/conversations",
        json={"knowledge_base_id": str(knowledge_base_id), "title": "Policy chat"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["knowledge_base_id"] == str(knowledge_base_id)
    assert response.json()["title"] == "Policy chat"


def test_list_conversations_route() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.get("/api/v1/conversations")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()[0]["title"] == "New chat"


def test_get_conversation_route() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)
    conversation_id = uuid4()

    response = client.get(f"/api/v1/conversations/{conversation_id}")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["id"] == str(conversation_id)
    assert response.json()["messages"][0]["source_chunks"][0]["filename"] == "policy.pdf"


def test_delete_conversation_route() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.delete(f"/api/v1/conversations/{uuid4()}")

    app.dependency_overrides.clear()
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_conversation_returns_404() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.delete(f"/api/v1/conversations/{MISSING_ID}")

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_create_conversation_message_route() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)
    conversation_id = uuid4()

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "What changed?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["user_message"]["content"] == "What changed?"
    assert body["assistant_message"]["content"].endswith("[1].")
    assert body["citations"][0]["filename"] == "policy.pdf"


def test_create_conversation_message_sse_route() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/conversations/{uuid4()}/messages",
        headers={"Accept": "text/event-stream"},
        json={"content": "What changed?", "limit": 5, "stream": True},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: message_start" in response.text
    assert "event: token" in response.text
    assert "event: sources" in response.text
    assert "event: message_done" in response.text


def test_record_message_feedback_route() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)
    message_id = uuid4()

    response = client.post(
        f"/api/v1/messages/{message_id}/feedback",
        json={"rating": "positive"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["message_id"] == str(message_id)
    assert response.json()["rating"] == "positive"


def test_record_message_feedback_missing_message_returns_404() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/messages/{MISSING_ID}/feedback",
        json={"rating": "negative"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_record_message_feedback_rejects_non_assistant_message() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/messages/00000000-0000-0000-0000-000000000400/feedback",
        json={"rating": "negative"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_record_message_feedback_validates_rating() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/messages/{uuid4()}/feedback",
        json={"rating": "mixed"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_create_conversation_missing_knowledge_base_returns_404() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/conversations",
        json={"knowledge_base_id": str(MISSING_ID), "title": "Policy chat"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_create_conversation_message_provider_error_returns_502() -> None:
    app.dependency_overrides[get_conversation_service] = lambda: FakeConversationService(
        error=ChatModelError("Gemini API key is not configured.")
    )
    client = TestClient(app)

    response = client.post(
        f"/api/v1/conversations/{uuid4()}/messages",
        json={"content": "What changed?", "limit": 5},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 502
