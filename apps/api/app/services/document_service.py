from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.document_parser import (
    DOCX_MIME_TYPE,
    PDF_MIME_TYPE,
    DocumentParser,
)
from app.rag.providers.embedding import EmbeddingProvider
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.document import DocumentRead
from app.schemas.retrieval import DocumentUploadRead
from app.services.document_processing_service import DocumentProcessingService

PDF_CONTENT_TYPES = {PDF_MIME_TYPE, "application/x-pdf"}
DOCX_CONTENT_TYPES = {DOCX_MIME_TYPE}
GENERIC_BINARY_CONTENT_TYPE = "application/octet-stream"
PDF_SIGNATURE = b"%PDF-"
DOCX_REQUIRED_MEMBERS = {"[Content_Types].xml", "word/document.xml"}
DOCX_MAIN_CONTENT_TYPE = (
    b"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)


@dataclass(frozen=True)
class DocumentContent:
    path: Path
    filename: str
    mime_type: str


class DocumentService:
    def __init__(
        self,
        *,
        session: Session,
        parsers: dict[str, DocumentParser],
        chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session = session
        self.parsers = parsers
        self.chunker = chunker
        self.embedding_provider = embedding_provider
        self.documents = DocumentRepository(session)
        self.knowledge_bases = KnowledgeBaseRepository(session)
        self.processor = DocumentProcessingService(
            documents=self.documents,
            parsers=self.parsers,
            chunker=self.chunker,
            embedding_provider=self.embedding_provider,
        )

    async def upload_document(
        self,
        *,
        knowledge_base_id: UUID,
        upload: UploadFile,
    ) -> DocumentUploadRead:
        knowledge_base = self.knowledge_bases.get(knowledge_base_id)
        if knowledge_base is None:
            raise LookupError("Knowledge base not found.")

        original_filename = upload.filename or "upload"
        content = await upload.read()
        mime_type = self._validate_document_upload(
            filename=original_filename,
            content_type=upload.content_type,
            content=content,
        )

        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self._safe_filename(original_filename)
        storage_key = f"{knowledge_base_id}/{uuid4()}-{safe_name}"
        target_path = upload_dir / storage_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)

        try:
            document = self.documents.create_pending(
                knowledge_base_id=knowledge_base_id,
                filename=safe_name,
                original_filename=original_filename,
                mime_type=mime_type,
                storage_key=storage_key,
            )
        except Exception:
            if target_path.exists():
                target_path.unlink()
            raise

        try:
            result = self.processor.process_document(document=document, target_path=target_path)
            self.session.commit()
            self.session.refresh(document)
            return DocumentUploadRead(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                status=document.status,
                page_count=document.page_count,
                chunk_count=result.chunk_count,
                error_message=document.error_message,
            )
        except Exception as exc:
            self.documents.mark_failed(document, error_message=str(exc))
            self.session.commit()
            self.session.refresh(document)
            return DocumentUploadRead(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                status=document.status,
                page_count=document.page_count,
                chunk_count=0,
                error_message=document.error_message,
            )

    def list_by_knowledge_base(self, knowledge_base_id: UUID) -> list[DocumentRead]:
        knowledge_base = self.knowledge_bases.get(knowledge_base_id)
        if knowledge_base is None:
            raise LookupError("Knowledge base not found.")
        return self.documents.list_by_knowledge_base(knowledge_base_id)

    def get(self, document_id: UUID) -> DocumentRead:
        document = self.documents.get_with_count(document_id)
        if document is None:
            raise LookupError("Document not found.")
        return document

    def get_content(
        self,
        document_id: UUID,
        *,
        allow_inactive_knowledge_base: bool,
    ) -> DocumentContent:
        document = self.documents.get(document_id)
        if document is None:
            raise LookupError("Document not found.")

        knowledge_base = self.knowledge_bases.get(document.knowledge_base_id)
        if knowledge_base is None or (
            not allow_inactive_knowledge_base and not knowledge_base.is_active
        ):
            raise LookupError("Document not found.")

        upload_root = Path(settings.upload_dir).resolve()
        target_path = (upload_root / document.storage_key).resolve()
        try:
            target_path.relative_to(upload_root)
        except ValueError as exc:
            raise LookupError("Document not found.") from exc

        if not target_path.is_file():
            raise LookupError("Document not found.")

        return DocumentContent(
            path=target_path,
            filename=document.original_filename,
            mime_type=document.mime_type,
        )

    def delete(self, document_id: UUID) -> None:
        document = self.documents.get(document_id)
        if document is None:
            raise LookupError("Document not found.")

        target_path = Path(settings.upload_dir) / document.storage_key
        self.documents.delete(document)
        self.session.commit()
        if target_path.exists():
            target_path.unlink()

    def reprocess(self, document_id: UUID) -> DocumentRead:
        document = self.documents.get(document_id)
        if document is None:
            raise LookupError("Document not found.")

        target_path = Path(settings.upload_dir) / document.storage_key
        try:
            self.processor.process_document(
                document=document,
                target_path=target_path,
                replace_existing=True,
            )
            self.session.commit()
            return self.get(document_id)
        except Exception as exc:
            self.documents.mark_failed(document, error_message=str(exc))
            self.session.commit()
            return self.get(document_id)

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-") or "upload"

    def _validate_document_upload(
        self,
        *,
        filename: str,
        content_type: str | None,
        content: bytes,
    ) -> str:
        extension = Path(filename).suffix.lower()
        normalized_content_type = (content_type or "").split(";", maxsplit=1)[0].lower()

        if extension not in {".pdf", ".docx"}:
            raise ValueError("Only PDF or DOCX uploads are supported.")

        if not content:
            raise ValueError("Uploaded document cannot be empty.")

        if len(content) > settings.max_upload_bytes:
            max_mb = settings.max_upload_bytes // (1024 * 1024)
            raise ValueError(f"Uploaded document must be {max_mb} MB or smaller.")

        if extension == ".pdf":
            if normalized_content_type not in PDF_CONTENT_TYPES | {GENERIC_BINARY_CONTENT_TYPE}:
                raise ValueError("File content type does not match its PDF extension.")
            if not content.startswith(PDF_SIGNATURE):
                raise ValueError("Uploaded file does not appear to be a valid PDF.")
            return PDF_MIME_TYPE

        if normalized_content_type not in DOCX_CONTENT_TYPES | {GENERIC_BINARY_CONTENT_TYPE}:
            raise ValueError("File content type does not match its DOCX extension.")
        self._validate_docx_archive(content)
        return DOCX_MIME_TYPE

    def _validate_docx_archive(self, content: bytes) -> None:
        try:
            with ZipFile(BytesIO(content)) as archive:
                members = archive.infolist()
                names = [member.filename for member in members]
                if len(names) != len(set(names)):
                    raise ValueError("Uploaded DOCX contains duplicate archive entries.")
                if any(member.flag_bits & 0x1 for member in members):
                    raise ValueError("Encrypted DOCX files are not supported.")
                if sum(member.file_size for member in members) > settings.max_docx_uncompressed_bytes:
                    max_mb = settings.max_docx_uncompressed_bytes // (1024 * 1024)
                    raise ValueError(
                        f"Uploaded DOCX must expand to {max_mb} MB or smaller."
                    )
                if not DOCX_REQUIRED_MEMBERS.issubset(names):
                    raise ValueError("Uploaded file does not appear to be a valid DOCX.")
                content_types = archive.read("[Content_Types].xml")
                if DOCX_MAIN_CONTENT_TYPE not in content_types:
                    raise ValueError("Uploaded file does not appear to be a valid DOCX.")
                if archive.testzip() is not None:
                    raise ValueError("Uploaded DOCX archive is corrupt.")
        except ValueError:
            raise
        except (BadZipFile, OSError, RuntimeError) as exc:
            raise ValueError("Uploaded file does not appear to be a valid DOCX.") from exc
