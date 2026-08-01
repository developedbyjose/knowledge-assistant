from __future__ import annotations

import re

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
HYPHENATED_LINE_BREAK = re.compile(r"(?<=\w)-\s*\n\s*(?=\w)")
LINE_BREAK = re.compile(r"\s*\n\s*")
WHITESPACE = re.compile(r"[ \t\r\f\v]+")


class PageCleaner:
    def clean(self, text: str | None) -> str:
        if not text:
            return ""

        cleaned = CONTROL_CHARS.sub(" ", text)
        cleaned = HYPHENATED_LINE_BREAK.sub("", cleaned)
        cleaned = LINE_BREAK.sub(" ", cleaned)
        cleaned = WHITESPACE.sub(" ", cleaned)
        return cleaned.strip()
