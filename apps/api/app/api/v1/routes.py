from __future__ import annotations

import json
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import (
    get_answer_service,
    get_conversation_service,
    get_document_service,
    get_knowledge_base_service,
    get_retrieval_service,
)
from app.rag.providers.chat import ChatModelError
from app.schemas.conversation import (
    ConversationCreate,
    ConversationMessageResponse,
    ConversationRead,
    MessageFeedbackCreate,
    MessageFeedbackRead,
    MessageCreate,
)
from app.schemas.document import DocumentRead
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.schemas.retrieval import CitedAnswer, DocumentUploadRead, RetrievalQuery, RetrievalResults
from app.services.answer_service import AnswerService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseRead])
def list_knowledge_bases(
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> list[KnowledgeBaseRead]:
    return service.list()


@router.post(
    "/knowledge-bases",
    response_model=KnowledgeBaseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    return service.create(name=payload.name, description=payload.description)


@router.get("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def get_knowledge_base(
    knowledge_base_id: UUID,
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    try:
        return service.get(knowledge_base_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def update_knowledge_base(
    knowledge_base_id: UUID,
    payload: KnowledgeBaseUpdate,
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    update_fields = payload.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Update payload cannot be empty.")
    if update_fields.get("name") is None and "name" in update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Knowledge base name cannot be null.")

    try:
        return service.update(knowledge_base_id=knowledge_base_id, values=update_fields)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/knowledge-bases/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    knowledge_base_id: UUID,
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> Response:
    try:
        service.delete(knowledge_base_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=DocumentUploadRead,
)
async def upload_document(
    knowledge_base_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
    file: UploadFile = File(...),
) -> DocumentUploadRead:
    try:
        return await service.upload_pdf(knowledge_base_id=knowledge_base_id, upload=file)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/knowledge-bases/{knowledge_base_id}/documents", response_model=list[DocumentRead])
def list_documents(
    knowledge_base_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentRead]:
    try:
        return service.list_by_knowledge_base(knowledge_base_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentRead:
    try:
        return service.get(document_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> Response:
    try:
        service.delete(document_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/documents/{document_id}/reprocess", response_model=DocumentRead)
def reprocess_document(
    document_id: UUID,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentRead:
    try:
        return service.reprocess(document_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _retrieve_chunks(
    knowledge_base_id: UUID,
    payload: RetrievalQuery,
    service: RetrievalService,
) -> RetrievalResults:
    try:
        return service.retrieve(
            knowledge_base_id=knowledge_base_id,
            question=payload.question,
            limit=payload.limit,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/knowledge-bases/{knowledge_base_id}/query-embedding",
    response_model=RetrievalResults,
)
def query_embedding(
    knowledge_base_id: UUID,
    payload: RetrievalQuery,
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> RetrievalResults:
    return _retrieve_chunks(knowledge_base_id, payload, service)


@router.post(
    "/knowledge-bases/{knowledge_base_id}/retrieval-query",
    response_model=RetrievalResults,
)
def retrieve_chunks(
    knowledge_base_id: UUID,
    payload: RetrievalQuery,
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> RetrievalResults:
    return _retrieve_chunks(knowledge_base_id, payload, service)


@router.post(
    "/knowledge-bases/{knowledge_base_id}/answers",
    response_model=CitedAnswer,
)
async def answer_question(
    knowledge_base_id: UUID,
    payload: RetrievalQuery,
    service: Annotated[AnswerService, Depends(get_answer_service)],
) -> CitedAnswer:
    try:
        return await service.answer(
            knowledge_base_id=knowledge_base_id,
            question=payload.question,
            limit=payload.limit,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ChatModelError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreate,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationRead:
    try:
        return service.create(knowledge_base_id=payload.knowledge_base_id, title=payload.title)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> list[ConversationRead]:
    return service.list()


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: UUID,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationRead:
    try:
        return service.get(conversation_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> Response:
    try:
        service.delete(conversation_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessageResponse,
)
async def create_conversation_message(
    conversation_id: UUID,
    payload: MessageCreate,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    accept: Annotated[Optional[str], Header()] = None,
) -> Any:
    wants_stream = payload.stream or (accept is not None and "text/event-stream" in accept)
    if wants_stream:
        return StreamingResponse(
            _format_sse(
                service.stream_message(
                    conversation_id=conversation_id,
                    content=payload.content,
                    limit=payload.limit,
                )
            ),
            media_type="text/event-stream",
        )

    try:
        return await service.add_message(
            conversation_id=conversation_id,
            content=payload.content,
            limit=payload.limit,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ChatModelError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/messages/{message_id}/feedback", response_model=MessageFeedbackRead)
def record_message_feedback(
    message_id: UUID,
    payload: MessageFeedbackCreate,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> MessageFeedbackRead:
    try:
        return service.record_feedback(message_id=message_id, rating=payload.rating)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


async def _format_sse(events):  # noqa: ANN001, ANN202
    async for event in events:
        yield f"event: {event['event']}\n"
        yield f"data: {json.dumps(event['data'])}\n\n"
