from __future__ import annotations

from dataclasses import dataclass

from app.rag.ingestion.document_parser import ParsedTextBlock


@dataclass(frozen=True)
class Chunk:
    chunk_index: int
    content: str
    page_number: int | None
    token_count: int
    metadata: dict[str, object]


class TextChunker:
    def __init__(self, *, chunk_size: int = 800, overlap: int = 150) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_blocks(self, blocks: list[ParsedTextBlock]) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = 0

        for block in blocks:
            words = block.text.split()
            if not words:
                continue
            source_metadata = dict(block.metadata)
            if block.page_number is not None:
                source_metadata.setdefault("source", "pdf")
                source_metadata.setdefault("page_number", block.page_number)

            start = 0
            while start < len(words):
                end = min(start + self.chunk_size, len(words))
                content = " ".join(words[start:end])
                token_count = len(content.split())
                chunks.append(
                    Chunk(
                        chunk_index=chunk_index,
                        content=content,
                        page_number=block.page_number,
                        token_count=token_count,
                        metadata={
                            **source_metadata,
                            "word_start": start,
                            "word_end": end,
                            "chunk_size": self.chunk_size,
                            "overlap": self.overlap,
                            "token_count": token_count,
                        },
                    )
                )
                chunk_index += 1

                if end == len(words):
                    break
                start = max(end - self.overlap, start + 1)

        return chunks

    def chunk_pages(self, pages: list[ParsedTextBlock]) -> list[Chunk]:
        return self.chunk_blocks(pages)
