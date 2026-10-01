from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.document_parser import DOCX_MIME_TYPE, PDF_MIME_TYPE
from app.rag.ingestion.docx_parser import DocxParser
from app.rag.ingestion.pdf_parser import PdfParser
from app.rag.providers.chat import ChatModel, ChatModelError
from app.rag.providers.factory import create_chat_model, create_embedding_provider
from app.rag.providers.embedding import EmbeddingProvider
from app.services.answer_service import AnswerService
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.retrieval_service import RetrievalService

SessionDep = Annotated[Session, Depends(get_session)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


def get_current_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    session_token: Annotated[Optional[str], Cookie(alias=settings.session_cookie_name)] = None,
):
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    user = service.current_user(session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return user


def require_current_user(user=Depends(get_current_user)):  # noqa: ANN001, ANN201, B008
    if user.must_change_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password change required.")
    return user


def require_admin(user=Depends(require_current_user)):  # noqa: ANN001, ANN201, B008
    if user.role not in {"admin", "superadmin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def require_superadmin(user=Depends(require_current_user)):  # noqa: ANN001, ANN201, B008
    if user.role != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin access required.")
    return user


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
        parsers={PDF_MIME_TYPE: PdfParser(), DOCX_MIME_TYPE: DocxParser()},
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
