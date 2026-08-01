from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


class PdfParser:
    def parse(self, path: Path) -> list[PageText]:
        reader = PdfReader(path)
        pages: list[PageText] = []

        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            normalized = " ".join(text.split())
            if normalized:
                pages.append(PageText(page_number=index, text=normalized))

        return pages
