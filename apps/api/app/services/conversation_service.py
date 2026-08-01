from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conversation import Conversation
from app.rag.generation.prompts import (
    NO_EVIDENCE_ANSWER,
    build_grounded_system_prompt,
    build_grounded_user_prompt,
)
from app.rag.providers.chat import ChatModel, ChatModelError
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.conversation import ConversationMessageResponse, ConversationRead, MessageRead
from app.schemas.retrieval import AnswerCitation, RetrievalResult
from app.services.answer_service import SOURCE_REFERENCE_PATTERN
from app.services.retrieval_service import RetrievalService


class ConversationService:
    def __init__(
        self,
        *,
        session: Session,
        retrieval_service: RetrievalService,
        chat_model: ChatModel,
    ) -> None:
        self.session = session
        self.retrieval_service = retrieval_service
        self.chat_model = chat_model
        self.conversations = ConversationRepository(session)
        self.knowledge_bases = KnowledgeBaseRepository(session)

    def create(self, *, knowledge_base_id: UUID, title: str | None) -> ConversationRead:
        if self.knowledge_bases.get(knowledge_base_id) is None:
            raise LookupError("Knowledge base not found.")
        conversation = self.conversations.create(
            knowledge_base_id=knowledge_base_id,
            title=_conversation_title(title),
        )
        self.session.commit()
        self.session.refresh(conversation)
        return ConversationRead.model_validate(conversation, from_attributes=True)

    def list(self) -> list[ConversationRead]:
        return [
            ConversationRead.model_validate(conversation, from_attributes=True)
            for conversation in self.conversations.list()
        ]

    def get(self, conversation_id: UUID) -> ConversationRead:
        conversation = self._get_required(conversation_id)
        return ConversationRead.model_validate(conversation, from_attributes=True)

    def delete(self, conversation_id: UUID) -> None:
        conversation = self._get_required(conversation_id)
        self.conversations.delete(conversation)
        self.session.commit()

    async def add_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
        limit: int,
    ) -> ConversationMessageResponse:
        conversation = self._get_required(conversation_id)
        user_message = self.conversations.add_message(
            conversation=conversation,
            role="user",
            content=content,
        )
        source_chunks = self._retrieve_usable_chunks(conversation=conversation, question=content, limit=limit)

        if not source_chunks:
            answer_text = NO_EVIDENCE_ANSWER
        else:
            answer_text = await self.chat_model.generate(
                system_prompt=build_grounded_system_prompt(),
                user_prompt=build_grounded_user_prompt(question=content, source_chunks=source_chunks),
            )

        citations = [] if not source_chunks else _citations_from_answer(answer=answer_text, source_chunks=source_chunks)
        assistant_message = self.conversations.add_message(
            conversation=conversation,
            role="assistant",
            content=answer_text,
            model_name=settings.llm_model,
        )
        self.session.commit()
        persisted = self._get_required(conversation_id)

        return ConversationMessageResponse(
            conversation=ConversationRead.model_validate(persisted, from_attributes=True),
            user_message=MessageRead.model_validate(user_message, from_attributes=True),
            assistant_message=MessageRead.model_validate(assistant_message, from_attributes=True),
            citations=citations,
            source_chunks=source_chunks,
        )

    async def stream_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
        limit: int,
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            conversation = self._get_required(conversation_id)
            user_message = self.conversations.add_message(
                conversation=conversation,
                role="user",
                content=content,
            )
            yield {
                "event": "message_start",
                "data": {
                    "conversation_id": str(conversation.id),
                    "user_message": MessageRead.model_validate(user_message, from_attributes=True).model_dump(mode="json"),
                },
            }

            source_chunks = self._retrieve_usable_chunks(conversation=conversation, question=content, limit=limit)
            if not source_chunks:
                answer_text = NO_EVIDENCE_ANSWER
                yield {"event": "token", "data": {"content": answer_text}}
                citations: list[AnswerCitation] = []
            else:
                answer_parts: list[str] = []
                async for token in self.chat_model.stream_generate(
                    system_prompt=build_grounded_system_prompt(),
                    user_prompt=build_grounded_user_prompt(question=content, source_chunks=source_chunks),
                ):
                    answer_parts.append(token)
                    yield {"event": "token", "data": {"content": token}}
                answer_text = "".join(answer_parts)
                citations = _citations_from_answer(answer=answer_text, source_chunks=source_chunks)

            assistant_message = self.conversations.add_message(
                conversation=conversation,
                role="assistant",
                content=answer_text,
                model_name=settings.llm_model,
            )
            self.session.commit()
            persisted = self._get_required(conversation_id)
            yield {
                "event": "sources",
                "data": {
                    "citations": [citation.model_dump(mode="json") for citation in citations],
                    "source_chunks": [chunk.model_dump(mode="json") for chunk in source_chunks],
                },
            }
            yield {
                "event": "message_done",
                "data": {
                    "conversation": ConversationRead.model_validate(persisted, from_attributes=True).model_dump(mode="json"),
                    "assistant_message": MessageRead.model_validate(assistant_message, from_attributes=True).model_dump(mode="json"),
                },
            }
        except (LookupError, ValueError, ChatModelError) as exc:
            self.session.rollback()
            yield {"event": "error", "data": {"detail": str(exc)}}

    def _get_required(self, conversation_id: UUID) -> Conversation:
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            raise LookupError("Conversation not found.")
        return conversation

    def _retrieve_usable_chunks(
        self,
        *,
        conversation: Conversation,
        question: str,
        limit: int,
    ) -> list[RetrievalResult]:
        retrieval = self.retrieval_service.retrieve(
            knowledge_base_id=conversation.knowledge_base_id,
            question=question,
            limit=limit,
        )
        chunks = retrieval.results
        if not chunks:
            return []
        if max(chunk.similarity_score for chunk in chunks) < settings.retrieval_min_similarity_score:
            return []
        return chunks


def _conversation_title(title: str | None) -> str:
    if title and title.strip():
        return title.strip()[:255]
    return "New chat"


def _citations_from_answer(
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
