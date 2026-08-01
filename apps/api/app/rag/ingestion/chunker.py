from __future__ import annotations

from dataclasses import dataclass

from app.rag.ingestion.pdf_parser import PageText


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

    def chunk_pages(self, pages: list[PageText]) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = 0

        for page in pages:
            words = page.text.split()
            if not words:
                continue

            start = 0
            while start < len(words):
                end = min(start + self.chunk_size, len(words))
                content = " ".join(words[start:end])
                token_count = len(content.split())
                chunks.append(
                    Chunk(
                        chunk_index=chunk_index,
                        content=content,
                        page_number=page.page_number,
                        token_count=token_count,
                        metadata={
                            "source": "pdf",
                            "page_number": page.page_number,
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
