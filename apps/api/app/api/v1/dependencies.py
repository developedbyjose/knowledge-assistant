from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.pdf_parser import PdfParser
from app.rag.providers.chat import ChatModel, ChatModelError
from app.rag.providers.factory import create_chat_model, create_embedding_provider
from app.rag.providers.embedding import EmbeddingProvider
from app.services.answer_service import AnswerService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.retrieval_service import RetrievalService

SessionDep = Annotated[Session, Depends(get_session)]


def get_embedding_provider() -> EmbeddingProvider:
    return create_embedding_provider()


def get_chat_model() -> ChatModel:
    try:
        return create_chat_model()
    except ChatModelError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


def get_knowledge_base_service(session: SessionDep) -> KnowledgeBaseService:
    return KnowledgeBaseService(session)


def get_document_service(
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> DocumentService:
    return DocumentService(
        session=session,
        parser=PdfParser(),
        chunker=TextChunker(),
        embedding_provider=embedding_provider,
    )


def get_retrieval_service(
    session: SessionDep,
    embedding_provider: Annotated[EmbeddingProvider, Depends(get_embedding_provider)],
) -> RetrievalService:
    return RetrievalService(session=session, embedding_provider=embedding_provider)


def get_answer_service(
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    chat_model: Annotated[ChatModel, Depends(get_chat_model)],
) -> AnswerService:
    return AnswerService(retrieval_service=retrieval_service, chat_model=chat_model)


def get_conversation_service(
    session: SessionDep,
    retrieval_service: Annotated[RetrievalService, Depends(get_retrieval_service)],
    chat_model: Annotated[ChatModel, Depends(get_chat_model)],
) -> ConversationService:
    return ConversationService(
        session=session,
        retrieval_service=retrieval_service,
        chat_model=chat_model,
    )
