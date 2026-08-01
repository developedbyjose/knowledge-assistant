from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation
from app.models.message import Message


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

    def list(self) -> list[Conversation]:
        statement = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get(self, conversation_id: UUID) -> Conversation | None:
        statement = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
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

    def delete(self, conversation: Conversation) -> None:
        self.session.delete(conversation)
        self.session.flush()
