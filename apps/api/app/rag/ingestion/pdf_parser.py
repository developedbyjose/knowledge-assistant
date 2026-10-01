from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from app.rag.ingestion.document_parser import ParsedTextBlock
from app.rag.ingestion.page_cleaner import PageCleaner

# Compatibility alias for existing imports while ingestion uses a format-neutral type.
PageText = ParsedTextBlock


class PdfParser:
    def __init__(self, *, page_cleaner: PageCleaner | None = None) -> None:
        self.page_cleaner = page_cleaner or PageCleaner()

    def parse(self, path: Path) -> list[ParsedTextBlock]:
        reader = PdfReader(path)
        pages: list[ParsedTextBlock] = []

        for index, page in enumerate(reader.pages, start=1):
            normalized = self.page_cleaner.clean(page.extract_text())
            if normalized:
                pages.append(
                    ParsedTextBlock(
                        page_number=index,
                        text=normalized,
                        metadata={"source": "pdf", "page_number": index},
                    )
                )

        return pages
