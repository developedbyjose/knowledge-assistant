from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@dataclass(frozen=True)
class ParsedTextBlock:
    text: str
    page_number: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)


class DocumentParser(Protocol):
    def parse(self, path: Path) -> list[ParsedTextBlock]: ...


def canonical_mime_type(mime_type: str) -> str | None:
    if mime_type in {PDF_MIME_TYPE, "application/x-pdf"}:
        return PDF_MIME_TYPE
    if mime_type == DOCX_MIME_TYPE:
        return DOCX_MIME_TYPE
    return None
