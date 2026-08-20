from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation
from app.models.document_chunk import DocumentChunk
from app.models.message import Message
from app.models.message_citation import MessageCitation
from app.models.message_feedback import MessageFeedback
from app.schemas.retrieval import AnswerCitation, RetrievalResult


class ConversationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        knowledge_base_id: UUID,
        title: str,
        user_id: UUID | None = None,
    ) -> Conversation:
        conversation = Conversation(
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            title=title,
        )
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def list(self, *, user_id: UUID) -> list[Conversation]:
        statement = (
            select(Conversation)
            .options(_message_load_options())
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get(self, conversation_id: UUID, *, user_id: UUID) -> Conversation | None:
        statement = (
            select(Conversation)
            .options(_message_load_options())
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return self.session.scalars(statement).one_or_none()

    def get_message(self, message_id: UUID, *, user_id: UUID) -> Message | None:
        statement = (
            select(Message)
            .options(
                selectinload(Message.citations)
                .selectinload(MessageCitation.chunk)
                .selectinload(DocumentChunk.document),
                selectinload(Message.feedback),
            )
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Message.id == message_id, Conversation.user_id == user_id)
        )
        return self.session.scalars(statement).one_or_none()

    def add_message(
        self,
        *,
        conversation: Conversation,
        role: str,
        content: str,
        model_name: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            model_name=model_name,
        )
        conversation.updated_at = datetime.now(timezone.utc)
        self.session.add(message)
        self.session.flush()
        return message

    def add_citations(
        self,
        *,
        message: Message,
        citations: list[AnswerCitation],
        source_chunks: list[RetrievalResult],
    ) -> list[MessageCitation]:
        chunks_by_id = {chunk.chunk_id: chunk for chunk in source_chunks}
        rows = []
        for citation in citations:
            source_chunk = chunks_by_id.get(citation.chunk_id)
            if source_chunk is None:
                continue
            rows.append(
                MessageCitation(
                    message_id=message.id,
                    chunk_id=citation.chunk_id,
                    rank=citation.rank,
                    similarity_score=source_chunk.similarity_score,
                    quoted_text=source_chunk.content,
                )
            )

        self.session.add_all(rows)
        self.session.flush()
        return rows

    def record_feedback(self, *, message: Message, rating: str) -> MessageFeedback:
        feedback = message.feedback
        if feedback is None:
            feedback = MessageFeedback(message_id=message.id, rating=rating)
            self.session.add(feedback)
        else:
            feedback.rating = rating
        self.session.flush()
        return feedback

    def delete(self, conversation: Conversation) -> None:
        self.session.delete(conversation)
        self.session.flush()


def _message_load_options():
    return selectinload(Conversation.messages).options(
        selectinload(Message.citations)
        .selectinload(MessageCitation.chunk)
        .selectinload(DocumentChunk.document),
        selectinload(Message.feedback),
    )
