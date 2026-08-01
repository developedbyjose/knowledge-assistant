from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.pdf_parser import PdfParser
from app.rag.providers.embedding import EmbeddingProvider
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.retrieval import DocumentUploadRead


class DocumentService:
    def __init__(
        self,
        *,
        session: Session,
        parser: PdfParser,
        chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session = session
        self.parser = parser
        self.chunker = chunker
        self.embedding_provider = embedding_provider
        self.documents = DocumentRepository(session)
        self.knowledge_bases = KnowledgeBaseRepository(session)

    async def upload_pdf(
        self,
        *,
        knowledge_base_id: UUID,
        upload: UploadFile,
    ) -> DocumentUploadRead:
        knowledge_base = self.knowledge_bases.get(knowledge_base_id)
        if knowledge_base is None:
            raise LookupError("Knowledge base not found.")

        if upload.content_type not in {"application/pdf", "application/x-pdf"}:
            raise ValueError("Only PDF uploads are supported.")

        original_filename = upload.filename or "upload.pdf"
        if not original_filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF uploads are supported.")

        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self._safe_filename(original_filename)
        storage_key = f"{knowledge_base_id}/{uuid4()}-{safe_name}"
        target_path = upload_dir / storage_key
        target_path.parent.mkdir(parents=True, exist_ok=True)

        content = await upload.read()
        target_path.write_bytes(content)

        document = self.documents.create_pending(
            knowledge_base_id=knowledge_base_id,
            filename=safe_name,
            original_filename=original_filename,
            mime_type=upload.content_type or "application/pdf",
            storage_key=storage_key,
        )

        try:
            self.documents.mark_processing(document)
            pages = self.parser.parse(target_path)
            chunks = self.chunker.chunk_pages(pages)
            if not chunks:
                raise ValueError("No extractable text was found in the PDF.")

            embeddings = self.embedding_provider.embed_texts([chunk.content for chunk in chunks])
            self.documents.add_chunks(document=document, chunks=chunks, embeddings=embeddings)
            self.documents.mark_processed(document, page_count=len(pages))
            self.session.commit()
            self.session.refresh(document)
            return DocumentUploadRead(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                status=document.status,
                page_count=document.page_count,
                chunk_count=len(chunks),
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

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-") or "upload.pdf"
