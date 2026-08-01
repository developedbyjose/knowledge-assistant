from app.rag.ingestion.page_cleaner import PageCleaner


def test_page_cleaner_removes_control_chars_and_repairs_hyphenated_lines() -> None:
    text = "A knowl-\nedge base\x00 page\n\nwith\tspacing."

    cleaned = PageCleaner().clean(text)

    assert cleaned == "A knowledge base page with spacing."
