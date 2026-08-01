from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.rag.ingestion.chunker import Chunk
from app.schemas.document import DocumentRead
from app.services import document_service as service_module
from app.services.document_service import DocumentService


@dataclass
class FakeDocument:
    id: UUID = field(default_factory=uuid4)
    knowledge_base_id: UUID = field(default_factory=uuid4)
    filename: str = "sample.pdf"
    original_filename: str = "sample.pdf"
    mime_type: str = "application/pdf"
    storage_key: str = ""
    status: str = "pending"
    page_count: int | None = None
    error_message: str | None = None


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1

    def refresh(self, document: FakeDocument) -> None:
        return None


class FakeKnowledgeBaseRepository:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def get(self, knowledge_base_id: UUID) -> object:
        return object()


class FakeDocumentRepository:
    created: list[FakeDocument] = []
    deleted: list[FakeDocument] = []
    documents_by_id: dict[UUID, FakeDocument] = {}

    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def create_pending(
        self,
        *,
        knowledge_base_id: UUID,
        filename: str,
        original_filename: str,
        mime_type: str,
        storage_key: str,
    ) -> FakeDocument:
        document = FakeDocument(
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            original_filename=original_filename,
            mime_type=mime_type,
            storage_key=storage_key,
        )
        self.created.append(document)
        self.documents_by_id[document.id] = document
        return document

    def mark_processing(self, document: FakeDocument) -> None:
        document.status = "processing"

    def mark_processed(self, document: FakeDocument, *, page_count: int) -> None:
        document.status = "processed"
        document.page_count = page_count
        document.error_message = None

    def mark_failed(self, document: FakeDocument, *, error_message: str) -> None:
        document.status = "failed"
        document.error_message = error_message

    def add_chunks(self, *, document: FakeDocument, chunks: list[Chunk], embeddings: list[list[float]]):  # noqa: ANN201
        return []

    def clear_chunks(self, document: FakeDocument) -> None:
        return None

    def get(self, document_id: UUID) -> FakeDocument | None:
        return self.documents_by_id.get(document_id)

    def delete(self, document: FakeDocument) -> None:
        self.deleted.append(document)
        self.documents_by_id.pop(document.id, None)

    def get_with_count(self, document_id: UUID) -> DocumentRead | None:
        document = self.documents_by_id.get(document_id)
        if document is None:
            return None
        return DocumentRead(
            id=document.id,
            knowledge_base_id=document.knowledge_base_id,
            filename=document.filename,
            original_filename=document.original_filename,
            mime_type=document.mime_type,
            status=document.status,
            page_count=document.page_count,
            chunk_count=0 if document.status == "failed" else 1,
            error_message=document.error_message,
            created_at="2026-08-01T00:00:00Z",
            processed_at=None,
        )


class FakeParser:
    def parse(self, path: Path):  # noqa: ANN201
        return [object()]


class FakeChunker:
    def chunk_pages(self, pages: list[object]) -> list[Chunk]:
        return [
            Chunk(
                chunk_index=0,
                content="A useful paragraph.",
                page_number=1,
                token_count=3,
                metadata={},
            )
        ]


class FakeEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def make_service() -> DocumentService:
    return DocumentService(
        session=FakeSession(),
        parser=FakeParser(),
        chunker=FakeChunker(),
        embedding_provider=FakeEmbeddingProvider(),
    )


def make_upload(
    content: bytes,
    *,
    filename: str = "sample.pdf",
    content_type: str = "application/pdf",
) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers=Headers({"content-type": content_type}),
    )


@pytest.fixture(autouse=True)
def fake_repositories(monkeypatch, tmp_path):  # noqa: ANN001, ANN201
    FakeDocumentRepository.created = []
    FakeDocumentRepository.deleted = []
    FakeDocumentRepository.documents_by_id = {}
    monkeypatch.setattr(service_module, "DocumentRepository", FakeDocumentRepository)
    monkeypatch.setattr(service_module, "KnowledgeBaseRepository", FakeKnowledgeBaseRepository)
    monkeypatch.setattr(service_module.settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(service_module.settings, "max_upload_bytes", 25)
    return tmp_path


def test_validation_failure_does_not_create_document_record() -> None:
    service = make_service()

    with pytest.raises(ValueError, match="valid PDF"):
        asyncio.run(service.upload_pdf(knowledge_base_id=uuid4(), upload=make_upload(b"not a pdf")))

    assert FakeDocumentRepository.created == []


def test_valid_upload_writes_file_locally(fake_repositories) -> None:  # noqa: ANN001
    service = make_service()
    knowledge_base_id = uuid4()

    result = asyncio.run(
        service.upload_pdf(
            knowledge_base_id=knowledge_base_id,
            upload=make_upload(b"%PDF-1.4 useful text"),
        )
    )

    assert result.status == "processed"
    document = FakeDocumentRepository.created[0]
    assert document.storage_key.startswith(f"{knowledge_base_id}/")
    assert (Path(fake_repositories) / document.storage_key).read_bytes() == b"%PDF-1.4 useful text"


def test_delete_removes_document_record_and_local_file(fake_repositories) -> None:  # noqa: ANN001
    service = make_service()
    document = FakeDocument(storage_key=f"{uuid4()}/sample.pdf")
    FakeDocumentRepository.documents_by_id[document.id] = document
    target_path = Path(fake_repositories) / document.storage_key
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(b"%PDF-1.4")

    service.delete(document.id)

    assert FakeDocumentRepository.deleted == [document]
    assert not target_path.exists()


def test_reprocess_uses_stored_file_and_marks_failed_when_missing() -> None:
    service = make_service()
    document = FakeDocument(status="processed", storage_key=f"{uuid4()}/missing.pdf")
    FakeDocumentRepository.documents_by_id[document.id] = document

    result = service.reprocess(document.id)

    assert result.status == "failed"
    assert result.error_message == "Stored document file not found."
