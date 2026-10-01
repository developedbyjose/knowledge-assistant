from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.rag.ingestion.chunker import Chunk
from app.rag.ingestion.document_parser import DOCX_MIME_TYPE, PDF_MIME_TYPE, ParsedTextBlock
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
    is_active = True

    def __init__(self, session: FakeSession) -> None:
        self.session = session

    def get(self, knowledge_base_id: UUID) -> object:
        return type("FakeKnowledgeBase", (), {"is_active": self.is_active})()


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

    def mark_processed(self, document: FakeDocument, *, page_count: int | None) -> None:
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
        return [ParsedTextBlock(text="A useful paragraph.", page_number=1)]


class FakeChunker:
    def chunk_blocks(self, blocks: list[ParsedTextBlock]) -> list[Chunk]:
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
    parser = FakeParser()
    return DocumentService(
        session=FakeSession(),
        parsers={PDF_MIME_TYPE: parser, DOCX_MIME_TYPE: parser},
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


def make_docx_archive(
    *,
    extra_uncompressed_bytes: int = 0,
    include_content_types: bool = True,
    include_document: bool = True,
    compression: int = ZIP_DEFLATED,
) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", compression=compression) as archive:
        if include_content_types:
            archive.writestr(
                "[Content_Types].xml",
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document.main+xml"/></Types>',
            )
        if include_document:
            archive.writestr("word/document.xml", b"<document/>" + (b"x" * extra_uncompressed_bytes))
    return output.getvalue()


def mark_first_zip_member_encrypted(content: bytes) -> bytes:
    modified = bytearray(content)
    central_header = modified.index(b"PK\x01\x02")
    flags_offset = central_header + 8
    flags = int.from_bytes(modified[flags_offset : flags_offset + 2], "little") | 0x1
    modified[flags_offset : flags_offset + 2] = flags.to_bytes(2, "little")
    return bytes(modified)


@pytest.fixture(autouse=True)
def fake_repositories(monkeypatch, tmp_path):  # noqa: ANN001, ANN201
    FakeDocumentRepository.created = []
    FakeDocumentRepository.deleted = []
    FakeDocumentRepository.documents_by_id = {}
    FakeKnowledgeBaseRepository.is_active = True
    monkeypatch.setattr(service_module, "DocumentRepository", FakeDocumentRepository)
    monkeypatch.setattr(service_module, "KnowledgeBaseRepository", FakeKnowledgeBaseRepository)
    monkeypatch.setattr(service_module.settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(service_module.settings, "max_upload_bytes", 1_024)
    monkeypatch.setattr(service_module.settings, "max_docx_uncompressed_bytes", 2_048)
    return tmp_path


def test_validation_failure_does_not_create_document_record() -> None:
    service = make_service()

    with pytest.raises(ValueError, match="valid PDF"):
        asyncio.run(
            service.upload_document(knowledge_base_id=uuid4(), upload=make_upload(b"not a pdf"))
        )

    assert FakeDocumentRepository.created == []


def test_valid_upload_writes_file_locally(fake_repositories) -> None:  # noqa: ANN001
    service = make_service()
    knowledge_base_id = uuid4()

    result = asyncio.run(
        service.upload_document(
            knowledge_base_id=knowledge_base_id,
            upload=make_upload(b"%PDF-1.4 useful text"),
        )
    )

    assert result.status == "processed"
    document = FakeDocumentRepository.created[0]
    assert document.storage_key.startswith(f"{knowledge_base_id}/")
    assert (Path(fake_repositories) / document.storage_key).read_bytes() == b"%PDF-1.4 useful text"


def test_valid_docx_upload_is_stored_with_canonical_mime_type(fake_repositories) -> None:  # noqa: ANN001
    service = make_service()
    content = make_docx_archive()

    result = asyncio.run(
        service.upload_document(
            knowledge_base_id=uuid4(),
            upload=make_upload(
                content,
                filename="handbook.docx",
                content_type="application/octet-stream",
            ),
        )
    )

    document = FakeDocumentRepository.created[0]
    assert result.status == "processed"
    assert result.page_count is None
    assert document.mime_type == DOCX_MIME_TYPE
    assert (Path(fake_repositories) / document.storage_key).read_bytes() == content


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "message"),
    [
        ("legacy.doc", "application/msword", b"legacy", "Only PDF or DOCX"),
        ("fake.pdf", "text/plain", b"%PDF-1.4", "does not match its PDF extension"),
        ("fake.docx", DOCX_MIME_TYPE, b"not a zip", "valid DOCX"),
        ("empty.pdf", PDF_MIME_TYPE, b"", "cannot be empty"),
    ],
)
def test_rejects_invalid_document_uploads(
    filename: str,
    content_type: str,
    content: bytes,
    message: str,
) -> None:
    service = make_service()

    with pytest.raises(ValueError, match=message):
        asyncio.run(
            service.upload_document(
                knowledge_base_id=uuid4(),
                upload=make_upload(content, filename=filename, content_type=content_type),
            )
        )

    assert FakeDocumentRepository.created == []


def test_rejects_docx_that_exceeds_uncompressed_limit(monkeypatch) -> None:  # noqa: ANN001
    service = make_service()
    content = make_docx_archive(extra_uncompressed_bytes=2_048)
    monkeypatch.setattr(service_module.settings, "max_upload_bytes", len(content) + 1)

    with pytest.raises(ValueError, match="expand to 0 MB or smaller"):
        asyncio.run(
            service.upload_document(
                knowledge_base_id=uuid4(),
                upload=make_upload(content, filename="large.docx", content_type=DOCX_MIME_TYPE),
            )
        )


def test_rejects_document_that_exceeds_upload_limit() -> None:
    service = make_service()

    with pytest.raises(ValueError, match="0 MB or smaller"):
        asyncio.run(
            service.upload_document(
                knowledge_base_id=uuid4(),
                upload=make_upload(b"%PDF-" + (b"x" * 1_024)),
            )
        )


def test_rejects_docx_missing_required_office_entries() -> None:
    service = make_service()
    content = make_docx_archive(include_document=False)

    with pytest.raises(ValueError, match="valid DOCX"):
        asyncio.run(
            service.upload_document(
                knowledge_base_id=uuid4(),
                upload=make_upload(content, filename="missing.docx", content_type=DOCX_MIME_TYPE),
            )
        )


def test_rejects_encrypted_docx_archive() -> None:
    service = make_service()
    content = mark_first_zip_member_encrypted(make_docx_archive())

    with pytest.raises(ValueError, match="Encrypted DOCX"):
        asyncio.run(
            service.upload_document(
                knowledge_base_id=uuid4(),
                upload=make_upload(content, filename="encrypted.docx", content_type=DOCX_MIME_TYPE),
            )
        )


def test_rejects_corrupt_docx_archive() -> None:
    service = make_service()
    content = make_docx_archive(compression=ZIP_STORED)
    corrupt = content.replace(b"<document/>", b"<documfnt/>", 1)

    with pytest.raises(ValueError, match="corrupt"):
        asyncio.run(
            service.upload_document(
                knowledge_base_id=uuid4(),
                upload=make_upload(corrupt, filename="corrupt.docx", content_type=DOCX_MIME_TYPE),
            )
        )


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


def test_get_content_returns_original_file_metadata(fake_repositories) -> None:  # noqa: ANN001
    service = make_service()
    document = FakeDocument(
        original_filename="Policy handbook.pdf",
        storage_key=f"{uuid4()}/policy.pdf",
    )
    FakeDocumentRepository.documents_by_id[document.id] = document
    target_path = Path(fake_repositories) / document.storage_key
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(b"%PDF-1.4")

    content = service.get_content(document.id, allow_inactive_knowledge_base=False)

    assert content.path == target_path.resolve()
    assert content.filename == "Policy handbook.pdf"
    assert content.mime_type == PDF_MIME_TYPE


def test_get_content_hides_document_in_inactive_knowledge_base(fake_repositories) -> None:  # noqa: ANN001
    service = make_service()
    document = FakeDocument(storage_key=f"{uuid4()}/sample.pdf")
    FakeDocumentRepository.documents_by_id[document.id] = document
    target_path = Path(fake_repositories) / document.storage_key
    target_path.parent.mkdir(parents=True)
    target_path.write_bytes(b"%PDF-1.4")
    FakeKnowledgeBaseRepository.is_active = False

    with pytest.raises(LookupError, match="Document not found"):
        service.get_content(document.id, allow_inactive_knowledge_base=False)

    assert service.get_content(
        document.id,
        allow_inactive_knowledge_base=True,
    ).path == target_path.resolve()


def test_get_content_rejects_path_outside_upload_root(fake_repositories, monkeypatch) -> None:  # noqa: ANN001
    upload_root = Path(fake_repositories) / "uploads"
    upload_root.mkdir()
    outside_file = Path(fake_repositories) / "outside.pdf"
    outside_file.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(service_module.settings, "upload_dir", str(upload_root))
    service = make_service()
    document = FakeDocument(storage_key="../outside.pdf")
    FakeDocumentRepository.documents_by_id[document.id] = document

    with pytest.raises(LookupError, match="Document not found"):
        service.get_content(document.id, allow_inactive_knowledge_base=True)


def test_get_content_hides_missing_stored_file() -> None:
    service = make_service()
    document = FakeDocument(storage_key=f"{uuid4()}/missing.pdf")
    FakeDocumentRepository.documents_by_id[document.id] = document

    with pytest.raises(LookupError, match="Document not found"):
        service.get_content(document.id, allow_inactive_knowledge_base=True)


def test_reprocess_uses_stored_file_and_marks_failed_when_missing() -> None:
    service = make_service()
    document = FakeDocument(status="processed", storage_key=f"{uuid4()}/missing.pdf")
    FakeDocumentRepository.documents_by_id[document.id] = document

    result = service.reprocess(document.id)

    assert result.status == "failed"
    assert result.error_message == "Stored document file not found."
