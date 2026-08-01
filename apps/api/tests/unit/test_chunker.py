from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.pdf_parser import PageText


def test_chunker_preserves_order_and_overlap() -> None:
    words = [f"word{i}" for i in range(25)]
    chunker = TextChunker(chunk_size=10, overlap=3)

    chunks = chunker.chunk_pages([PageText(page_number=1, text=" ".join(words))])

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2, 3]
    assert chunks[0].content.split()[-3:] == chunks[1].content.split()[:3]
    assert chunks[1].content.split()[-3:] == chunks[2].content.split()[:3]
    assert all(chunk.page_number == 1 for chunk in chunks)
    assert chunks[0].metadata == {
        "source": "pdf",
        "page_number": 1,
        "word_start": 0,
        "word_end": 10,
        "chunk_size": 10,
        "overlap": 3,
        "token_count": 10,
    }
