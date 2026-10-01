from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.rag.ingestion.document_parser import ParsedTextBlock
from app.rag.ingestion.page_cleaner import PageCleaner


class DocxParser:
    def __init__(self, *, page_cleaner: PageCleaner | None = None) -> None:
        self.page_cleaner = page_cleaner or PageCleaner()

    def parse(self, path: Path) -> list[ParsedTextBlock]:
        document = Document(path)
        blocks: list[ParsedTextBlock] = []

        for block_index, item in enumerate(document.iter_inner_content()):
            if isinstance(item, Paragraph):
                text = self.page_cleaner.clean(item.text)
                block_type = "paragraph"
            elif isinstance(item, Table):
                rows = [
                    " | ".join(cell.text for cell in row.cells)
                    for row in item.rows
                ]
                text = self.page_cleaner.clean("\n".join(rows))
                block_type = "table"
            else:
                continue

            if text:
                blocks.append(
                    ParsedTextBlock(
                        text=text,
                        metadata={
                            "source": "docx",
                            "block_type": block_type,
                            "block_index": block_index,
                        },
                    )
                )

        return blocks
