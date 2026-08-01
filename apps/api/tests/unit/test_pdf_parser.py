from pathlib import Path

from app.rag.ingestion.pdf_parser import PdfParser


class FakePage:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class FakeReader:
    def __init__(self, path: Path) -> None:
        self.pages = [FakePage(" First page text. "), FakePage("")]


def test_pdf_parser_extracts_non_empty_page_text(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr("app.rag.ingestion.pdf_parser.PdfReader", FakeReader)

    pages = PdfParser().parse(Path("sample.pdf"))

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].text == "First page text."
