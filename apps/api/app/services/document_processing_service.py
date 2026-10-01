from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.document import Document
from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.document_parser import (
    PDF_MIME_TYPE,
    DocumentParser,
    canonical_mime_type,
)
from app.rag.providers.embedding import EmbeddingProvider
from app.repositories.document_repository import DocumentRepository


@dataclass(frozen=True)
class DocumentProcessingResult:
    page_count: int | None
    chunk_count: int


class DocumentProcessingService:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        parsers: dict[str, DocumentParser],
        chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.documents = documents
        self.parsers = parsers
        self.chunker = chunker
        self.embedding_provider = embedding_provider

    def process_document(
        self,
        *,
        document: Document,
        target_path: Path,
        replace_existing: bool = False,
    ) -> DocumentProcessingResult:
        self.documents.mark_processing(document)
        if replace_existing:
            self.documents.clear_chunks(document)

        if not target_path.exists():
            raise FileNotFoundError("Stored document file not found.")

        mime_type = canonical_mime_type(document.mime_type)
        parser = self.parsers.get(mime_type or "")
        if parser is None:
            raise ValueError("Stored document type is not supported.")

        blocks = parser.parse(target_path)
        chunks = self.chunker.chunk_blocks(blocks)
        if not chunks:
            raise ValueError("No extractable text was found in the document.")

        embeddings = self.embedding_provider.embed_texts([chunk.content for chunk in chunks])
        self.documents.add_chunks(document=document, chunks=chunks, embeddings=embeddings)
        page_count = len(blocks) if mime_type == PDF_MIME_TYPE else None
        self.documents.mark_processed(document, page_count=page_count)
        return DocumentProcessingResult(page_count=page_count, chunk_count=len(chunks))
