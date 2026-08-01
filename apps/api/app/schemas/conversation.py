from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.retrieval import AnswerCitation, RetrievalResult

MessageRole = Literal["user", "assistant", "system"]
FeedbackRating = Literal["positive", "negative"]


class ConversationCreate(BaseModel):
    knowledge_base_id: UUID
    title: Optional[str] = Field(default=None, max_length=255)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)
    stream: bool = False


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    model_name: Optional[str]
    created_at: datetime
    citations: list[AnswerCitation] = Field(default_factory=list)
    source_chunks: list[RetrievalResult] = Field(default_factory=list)
    feedback_rating: Optional[FeedbackRating] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationRead(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    knowledge_base_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ConversationMessageResponse(BaseModel):
    conversation: ConversationRead
    user_message: MessageRead
    assistant_message: MessageRead
    citations: list[AnswerCitation]
    source_chunks: list[RetrievalResult]


class MessageFeedbackCreate(BaseModel):
    rating: FeedbackRating


class MessageFeedbackRead(BaseModel):
    id: UUID
    message_id: UUID
    rating: FeedbackRating
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
