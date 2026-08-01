from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.dependencies import (
    get_document_service,
    get_knowledge_base_service,
    get_retrieval_service,
)
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead
from app.schemas.retrieval import DocumentUploadRead, RetrievalQuery, RetrievalResults
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


@router.post(
    "/knowledge-bases/{knowledge_base_id}/retrieval-query",
    response_model=RetrievalResults,
)
def retrieve_chunks(
    knowledge_base_id: UUID,
    payload: RetrievalQuery,
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> RetrievalResults:
    try:
        return service.retrieve(
            knowledge_base_id=knowledge_base_id,
            question=payload.question,
            limit=payload.limit,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
