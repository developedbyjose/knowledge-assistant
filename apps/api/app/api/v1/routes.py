from __future__ import annotations

import json
from typing import Annotated, Any, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, File, Header, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from app.api.v1.dependencies import (
    get_answer_service, get_auth_service, get_conversation_service, get_current_user,
    get_document_service, get_knowledge_base_service, get_retrieval_service,
    require_admin, require_current_user, require_superadmin,
)
from app.core.config import settings
from app.models.user import User
from app.rag.providers.chat import ChatModelError
from app.schemas.auth import (
    ChangePasswordRequest, LoginRequest, LoginResponse, PasswordResetRequest,
    UserCreate, UserRead, UserUpdate,
)
from app.schemas.conversation import (
    ConversationCreate, ConversationMessageResponse, ConversationRead, MessageCreate,
    MessageFeedbackCreate, MessageFeedbackRead,
)
from app.schemas.document import DocumentRead
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.schemas.retrieval import CitedAnswer, DocumentUploadRead, RetrievalQuery, RetrievalResults
from app.services.answer_service import AnswerService
from app.services.auth_service import AuthService, AuthenticationError
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/api/v1")
CurrentUser = Annotated[User, Depends(require_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
SuperadminUser = Annotated[User, Depends(require_superadmin)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, service: Annotated[AuthService, Depends(get_auth_service)]) -> LoginResponse:
    try:
        user = service.authenticate(email=payload.email, password=payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _set_session_cookie(response, service.create_session(user))
    return LoginResponse(user=UserRead.model_validate(user), must_change_password=user.must_change_password)


@router.post("/auth/logout", status_code=204)
def logout(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _: Annotated[User, Depends(get_current_user)],
    session_token: Annotated[Optional[str], Cookie(alias=settings.session_cookie_name)] = None,
) -> Response:
    if session_token:
        service.logout(session_token)
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.status_code = 204
    return response


@router.get("/auth/me", response_model=UserRead)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead.model_validate(user)


@router.post("/auth/change-password", response_model=LoginResponse)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    try:
        token = service.change_password(user=user, current_password=payload.current_password, new_password=payload.new_password)
    except (AuthenticationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _set_session_cookie(response, token)
    return LoginResponse(user=UserRead.model_validate(user), must_change_password=False)


@router.get("/users", response_model=list[UserRead])
def list_users(_: SuperadminUser, service: Annotated[AuthService, Depends(get_auth_service)]) -> list[UserRead]:
    return service.list_users()


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, _: SuperadminUser, service: Annotated[AuthService, Depends(get_auth_service)]) -> UserRead:
    try:
        return service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, _: SuperadminUser, service: Annotated[AuthService, Depends(get_auth_service)]) -> UserRead:
    try:
        return service.get_user(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID, payload: UserUpdate, actor: SuperadminUser,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    try:
        return service.update_user(actor=actor, user_id=user_id, payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/users/{user_id}/reset-password", response_model=UserRead)
def reset_user_password(
    user_id: UUID, payload: PasswordResetRequest, _: SuperadminUser,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    try:
        return service.reset_password(user_id=user_id, temporary_password=payload.temporary_password)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseRead])
def list_knowledge_bases(user: CurrentUser, service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)]) -> list[KnowledgeBaseRead]:
    return service.list(active_only=user.role == "user")


@router.post("/knowledge-bases", response_model=KnowledgeBaseRead, status_code=201)
def create_knowledge_base(payload: KnowledgeBaseCreate, _: AdminUser, service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)]) -> KnowledgeBaseRead:
    return service.create(name=payload.name, description=payload.description)


@router.get("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def get_knowledge_base(
    knowledge_base_id: UUID, user: CurrentUser,
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    try:
        knowledge_base = service.get(knowledge_base_id)
        if user.role == "user" and not knowledge_base.is_active:
            raise LookupError("Knowledge base not found.")
        return knowledge_base
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def update_knowledge_base(
    knowledge_base_id: UUID, payload: KnowledgeBaseUpdate, _: AdminUser,
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    values = payload.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="Update payload cannot be empty.")
    if values.get("name") is None and "name" in values:
        raise HTTPException(status_code=400, detail="Knowledge base name cannot be null.")
    try:
        return service.update(knowledge_base_id=knowledge_base_id, values=values)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/knowledge-bases/{knowledge_base_id}", status_code=204)
def delete_knowledge_base(knowledge_base_id: UUID, _: AdminUser, service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)]) -> Response:
    try:
        service.delete(knowledge_base_id)
        return Response(status_code=204)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/knowledge-bases/{knowledge_base_id}/documents", response_model=DocumentUploadRead)
async def upload_document(
    knowledge_base_id: UUID, _: AdminUser,
    service: Annotated[DocumentService, Depends(get_document_service)], file: UploadFile = File(...),
) -> DocumentUploadRead:
    try:
        return await service.upload_document(knowledge_base_id=knowledge_base_id, upload=file)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/knowledge-bases/{knowledge_base_id}/documents", response_model=list[DocumentRead])
def list_documents(knowledge_base_id: UUID, _: AdminUser, service: Annotated[DocumentService, Depends(get_document_service)]) -> list[DocumentRead]:
    try:
        return service.list_by_knowledge_base(knowledge_base_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: UUID, _: AdminUser, service: Annotated[DocumentService, Depends(get_document_service)]) -> DocumentRead:
    try:
        return service.get(document_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/documents/{document_id}/content", response_class=FileResponse)
def get_document_content(
    document_id: UUID,
    user: CurrentUser,
    service: Annotated[DocumentService, Depends(get_document_service)],
    disposition: Literal["inline", "attachment"] = "inline",
) -> FileResponse:
    try:
        content = service.get_content(
            document_id,
            allow_inactive_knowledge_base=user.role in {"admin", "superadmin"},
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc

    return FileResponse(
        path=content.path,
        media_type=content.mime_type,
        filename=content.filename,
        content_disposition_type=disposition,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: UUID, _: AdminUser, service: Annotated[DocumentService, Depends(get_document_service)]) -> Response:
    try:
        service.delete(document_id)
        return Response(status_code=204)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/documents/{document_id}/reprocess", response_model=DocumentRead)
def reprocess_document(document_id: UUID, _: AdminUser, service: Annotated[DocumentService, Depends(get_document_service)]) -> DocumentRead:
    try:
        return service.reprocess(document_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _retrieve_chunks(knowledge_base_id: UUID, payload: RetrievalQuery, service: RetrievalService) -> RetrievalResults:
    try:
        return service.retrieve(knowledge_base_id=knowledge_base_id, question=payload.question, limit=payload.limit)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/knowledge-bases/{knowledge_base_id}/query-embedding", response_model=RetrievalResults)
def query_embedding(knowledge_base_id: UUID, payload: RetrievalQuery, _: AdminUser, service: Annotated[RetrievalService, Depends(get_retrieval_service)]) -> RetrievalResults:
    return _retrieve_chunks(knowledge_base_id, payload, service)


@router.post("/knowledge-bases/{knowledge_base_id}/retrieval-query", response_model=RetrievalResults)
def retrieve_chunks(knowledge_base_id: UUID, payload: RetrievalQuery, _: AdminUser, service: Annotated[RetrievalService, Depends(get_retrieval_service)]) -> RetrievalResults:
    return _retrieve_chunks(knowledge_base_id, payload, service)


@router.post("/knowledge-bases/{knowledge_base_id}/answers", response_model=CitedAnswer)
async def answer_question(knowledge_base_id: UUID, payload: RetrievalQuery, _: AdminUser, service: Annotated[AnswerService, Depends(get_answer_service)]) -> CitedAnswer:
    try:
        return await service.answer(knowledge_base_id=knowledge_base_id, question=payload.question, limit=payload.limit)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ChatModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/conversations", response_model=ConversationRead, status_code=201)
def create_conversation(payload: ConversationCreate, user: CurrentUser, service: Annotated[ConversationService, Depends(get_conversation_service)]) -> ConversationRead:
    try:
        return service.create(user_id=user.id, knowledge_base_id=payload.knowledge_base_id, title=payload.title)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(user: CurrentUser, service: Annotated[ConversationService, Depends(get_conversation_service)]) -> list[ConversationRead]:
    return service.list(user_id=user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: UUID, user: CurrentUser, service: Annotated[ConversationService, Depends(get_conversation_service)]) -> ConversationRead:
    try:
        return service.get(conversation_id, user_id=user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: UUID, user: CurrentUser, service: Annotated[ConversationService, Depends(get_conversation_service)]) -> Response:
    try:
        service.delete(conversation_id, user_id=user.id)
        return Response(status_code=204)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationMessageResponse)
async def create_conversation_message(
    conversation_id: UUID, payload: MessageCreate, user: CurrentUser,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    accept: Annotated[Optional[str], Header()] = None,
) -> Any:
    try:
        service.authorize_message(conversation_id=conversation_id, user_id=user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if payload.stream or (accept is not None and "text/event-stream" in accept):
        return StreamingResponse(
            _format_sse(service.stream_message(conversation_id=conversation_id, user_id=user.id, content=payload.content, limit=payload.limit)),
            media_type="text/event-stream",
        )
    try:
        return await service.add_message(conversation_id=conversation_id, user_id=user.id, content=payload.content, limit=payload.limit)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ChatModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/messages/{message_id}/feedback", response_model=MessageFeedbackRead)
def record_message_feedback(message_id: UUID, payload: MessageFeedbackCreate, user: CurrentUser, service: Annotated[ConversationService, Depends(get_conversation_service)]) -> MessageFeedbackRead:
    try:
        return service.record_feedback(message_id=message_id, user_id=user.id, rating=payload.rating)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name, value=token,
        max_age=settings.session_lifetime_days * 24 * 60 * 60,
        httponly=True, secure=settings.session_cookie_secure, samesite="lax", path="/",
    )


async def _format_sse(events):  # noqa: ANN001, ANN202
    async for event in events:
        yield f"event: {event['event']}\n"
        yield f"data: {json.dumps(event['data'])}\n\n"
