from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID, uuid4

from app.rag.ingestion.chunker import Chunk
from app.rag.ingestion.document_parser import DOCX_MIME_TYPE, PDF_MIME_TYPE, ParsedTextBlock
from app.services.document_processing_service import DocumentProcessingService


@dataclass
class FakeDocument:
    id: UUID = field(default_factory=uuid4)
    status: str = "pending"
    page_count: int | None = None
    mime_type: str = PDF_MIME_TYPE


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.added_chunks: list[Chunk] = []
        self.added_embeddings: list[list[float]] = []
        self.cleared = False

    def mark_processing(self, document: FakeDocument) -> None:
        document.status = "processing"

    def clear_chunks(self, document: FakeDocument) -> None:
        self.cleared = True

    def add_chunks(
        self,
        *,
        document: FakeDocument,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        self.added_chunks = chunks
        self.added_embeddings = embeddings

    def mark_processed(self, document: FakeDocument, *, page_count: int | None) -> None:
        document.status = "processed"
        document.page_count = page_count


class FakeParser:
    def parse(self, path: Path) -> list[ParsedTextBlock]:
        return [ParsedTextBlock(page_number=1, text="alpha beta gamma")]


class FakeChunker:
    def chunk_blocks(self, blocks: list[ParsedTextBlock]) -> list[Chunk]:
        return [
            Chunk(
                chunk_index=0,
                content=blocks[0].text,
                page_number=blocks[0].page_number,
                token_count=3,
                metadata={"page_number": 1},
            )
        ]


class FakeEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


def test_document_processing_extracts_chunks_embeds_and_marks_processed(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "sample.pdf"
    path.write_bytes(b"%PDF-1.4")
    document = FakeDocument()
    repository = FakeDocumentRepository()
    service = DocumentProcessingService(
        documents=repository,
        parsers={PDF_MIME_TYPE: FakeParser(), DOCX_MIME_TYPE: FakeParser()},
        chunker=FakeChunker(),
        embedding_provider=FakeEmbeddingProvider(),
    )

    result = service.process_document(document=document, target_path=path, replace_existing=True)

    assert result.page_count == 1
    assert result.chunk_count == 1
    assert document.status == "processed"
    assert document.page_count == 1
    assert repository.cleared is True
    assert repository.added_chunks[0].content == "alpha beta gamma"
    assert repository.added_embeddings == [[0.1, 0.2, 0.3]]


def test_docx_processing_does_not_fabricate_page_count(tmp_path) -> None:  # noqa: ANN001
    path = tmp_path / "sample.docx"
    path.write_bytes(b"stored docx")
    document = FakeDocument(mime_type=DOCX_MIME_TYPE)
    repository = FakeDocumentRepository()
    service = DocumentProcessingService(
        documents=repository,
        parsers={PDF_MIME_TYPE: FakeParser(), DOCX_MIME_TYPE: FakeParser()},
        chunker=FakeChunker(),
        embedding_provider=FakeEmbeddingProvider(),
    )

    result = service.process_document(document=document, target_path=path)

    assert result.page_count is None
    assert document.page_count is None
