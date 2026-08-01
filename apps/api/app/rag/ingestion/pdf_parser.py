from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app.rag.ingestion.page_cleaner import PageCleaner


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


class PdfParser:
    def __init__(self, *, page_cleaner: PageCleaner | None = None) -> None:
        self.page_cleaner = page_cleaner or PageCleaner()

    def parse(self, path: Path) -> list[PageText]:
        reader = PdfReader(path)
        pages: list[PageText] = []

        for index, page in enumerate(reader.pages, start=1):
            normalized = self.page_cleaner.clean(page.extract_text())
            if normalized:
                pages.append(PageText(page_number=index, text=normalized))

        return pages
