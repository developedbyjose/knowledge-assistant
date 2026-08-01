from __future__ import annotations

import re
from uuid import UUID

from app.core.config import settings
from app.rag.generation.prompts import (
    NO_EVIDENCE_ANSWER,
    build_grounded_system_prompt,
    build_grounded_user_prompt,
)
from app.rag.providers.chat import ChatModel
from app.schemas.retrieval import AnswerCitation, CitedAnswer, RetrievalResult
from app.services.retrieval_service import RetrievalService

SOURCE_REFERENCE_PATTERN = re.compile(r"\[(?:source:)?\s*(\d+)\]", re.IGNORECASE)


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
        source_chunks = self._usable_chunks(retrieval_results.results)
        if not source_chunks:
            return CitedAnswer(
                question=question,
                answer=NO_EVIDENCE_ANSWER,
                citations=[],
                source_chunks=[],
            )

        answer_text = await self.chat_model.generate(
            system_prompt=build_grounded_system_prompt(),
            user_prompt=build_grounded_user_prompt(question=question, source_chunks=source_chunks),
        )

        return CitedAnswer(
            question=question,
            answer=answer_text,
            citations=self._citations_from_answer(answer=answer_text, source_chunks=source_chunks),
            source_chunks=source_chunks,
        )

    def _usable_chunks(self, source_chunks: list[RetrievalResult]) -> list[RetrievalResult]:
        if not source_chunks:
            return []
        if max(chunk.similarity_score for chunk in source_chunks) < settings.retrieval_min_similarity_score:
            return []
        return source_chunks

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
