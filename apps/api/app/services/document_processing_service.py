from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.document import Document
from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.pdf_parser import PdfParser
from app.rag.providers.embedding import EmbeddingProvider
from app.repositories.document_repository import DocumentRepository


@dataclass(frozen=True)
class DocumentProcessingResult:
    page_count: int
    chunk_count: int


class DocumentProcessingService:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        parser: PdfParser,
        chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.documents = documents
        self.parser = parser
        self.chunker = chunker
        self.embedding_provider = embedding_provider

    def process_pdf(
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

        pages = self.parser.parse(target_path)
        chunks = self.chunker.chunk_pages(pages)
        if not chunks:
            raise ValueError("No extractable text was found in the PDF.")

        embeddings = self.embedding_provider.embed_texts([chunk.content for chunk in chunks])
        self.documents.add_chunks(document=document, chunks=chunks, embeddings=embeddings)
        self.documents.mark_processed(document, page_count=len(pages))
        return DocumentProcessingResult(page_count=len(pages), chunk_count=len(chunks))
