from __future__ import annotations

from app.schemas.retrieval import RetrievalResult

NO_EVIDENCE_ANSWER = (
    "I could not find enough relevant evidence in this knowledge base to answer the question."
)


def build_grounded_system_prompt() -> str:
    return (
        "You answer questions for a knowledge assistant using only the provided sources. "
        "Do not use outside knowledge. If the sources do not contain enough evidence, say "
        "you do not have enough evidence. Cite every factual claim with bracketed source "
        "numbers like [1]."
    )


def build_grounded_user_prompt(
    *,
    question: str,
    source_chunks: list[RetrievalResult],
) -> str:
    sources = "\n\n".join(
        (
            f"[{index}] filename={chunk.filename}; document_id={chunk.document_id}; "
            f"chunk_id={chunk.chunk_id}; page={chunk.page_number}; "
            f"chunk_index={chunk.chunk_index}; rank={chunk.rank}; "
            f"similarity_score={chunk.similarity_score:.4f}; metadata={chunk.metadata}\n"
            f"{chunk.content}"
        )
        for index, chunk in enumerate(source_chunks, start=1)
    )
    return f"Question:\n{question}\n\nSources:\n{sources}"
