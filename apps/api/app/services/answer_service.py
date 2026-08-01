from __future__ import annotations

import re
from uuid import UUID

from app.rag.providers.chat import ChatModel
from app.schemas.retrieval import AnswerCitation, CitedAnswer, RetrievalResult
from app.services.retrieval_service import RetrievalService

SOURCE_REFERENCE_PATTERN = re.compile(r"\[(?:source:)?\s*(\d+)\]", re.IGNORECASE)

NO_EVIDENCE_ANSWER = (
    "I could not find enough relevant evidence in this knowledge base to answer the question."
)


class AnswerService:
    def __init__(
        self,
        *,
        retrieval_service: RetrievalService,
        chat_model: ChatModel,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.chat_model = chat_model

    async def answer(
        self,
        *,
        knowledge_base_id: UUID,
        question: str,
        limit: int = 5,
    ) -> CitedAnswer:
        retrieval_results = self.retrieval_service.retrieve(
            knowledge_base_id=knowledge_base_id,
            question=question,
            limit=limit,
        )
        source_chunks = retrieval_results.results
        if not source_chunks:
            return CitedAnswer(
                question=question,
                answer=NO_EVIDENCE_ANSWER,
                citations=[],
                source_chunks=[],
            )

        answer_text = await self.chat_model.generate(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(question=question, source_chunks=source_chunks),
        )

        return CitedAnswer(
            question=question,
            answer=answer_text,
            citations=self._citations_from_answer(answer=answer_text, source_chunks=source_chunks),
            source_chunks=source_chunks,
        )

    def _build_system_prompt(self) -> str:
        return (
            "You answer questions for a knowledge assistant using only the provided sources. "
            "If the sources do not contain the answer, say you do not have enough evidence. "
            "Cite every factual claim with bracketed source numbers like [1]."
        )

    def _build_user_prompt(
        self,
        *,
        question: str,
        source_chunks: list[RetrievalResult],
    ) -> str:
        sources = "\n\n".join(
            (
                f"[{index}] filename={chunk.filename}; document_id={chunk.document_id}; "
                f"chunk_id={chunk.chunk_id}; page={chunk.page_number}; "
                f"chunk_index={chunk.chunk_index}; rank={chunk.rank}\n{chunk.content}"
            )
            for index, chunk in enumerate(source_chunks, start=1)
        )
        return f"Question:\n{question}\n\nSources:\n{sources}"

    def _citations_from_answer(
        self,
        *,
        answer: str,
        source_chunks: list[RetrievalResult],
    ) -> list[AnswerCitation]:
        referenced_numbers = [
            int(match.group(1))
            for match in SOURCE_REFERENCE_PATTERN.finditer(answer)
            if 1 <= int(match.group(1)) <= len(source_chunks)
        ]
        if not referenced_numbers:
            referenced_numbers = [1]

        seen: set[int] = set()
        citations: list[AnswerCitation] = []
        for source_number in referenced_numbers:
            if source_number in seen:
                continue
            seen.add(source_number)
            chunk = source_chunks[source_number - 1]
            citations.append(
                AnswerCitation(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    rank=chunk.rank,
                )
            )

        return citations
