import asyncio
from uuid import UUID, uuid4

import pytest

from app.rag.providers.chat import ChatModelError
from app.schemas.retrieval import RetrievalResult, RetrievalResults
from app.services.answer_service import AnswerService, NO_EVIDENCE_ANSWER


class FakeRetrievalService:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self.results = results
        self.calls: list[dict[str, object]] = []

    def retrieve(
        self,
        *,
        knowledge_base_id: UUID,
        question: str,
        limit: int,
    ) -> RetrievalResults:
        self.calls.append(
            {
                "knowledge_base_id": knowledge_base_id,
                "question": question,
                "limit": limit,
            }
        )
        return RetrievalResults(question=question, results=self.results)


class FakeChatModel:
    def __init__(self, answer: str = "Use the policy chunks [1].") -> None:
        self.answer = answer
        self.calls: list[dict[str, str]] = []

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return self.answer


class FailingChatModel:
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        raise ChatModelError("Provider unavailable.")


def _result(*, rank: int, filename: str = "policy.pdf") -> RetrievalResult:
    return RetrievalResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename=filename,
        rank=rank,
        similarity_score=0.9,
        content=f"Evidence for source {rank}.",
        page_number=rank,
        chunk_index=rank - 1,
        metadata={"page_number": rank},
    )


def test_answer_builds_grounded_prompt_and_maps_citations() -> None:
    chunks = [_result(rank=1), _result(rank=2, filename="ops.pdf")]
    retrieval_service = FakeRetrievalService(chunks)
    chat_model = FakeChatModel("The answer combines two facts [2] and [1].")
    service = AnswerService(
        retrieval_service=retrieval_service,  # type: ignore[arg-type]
        chat_model=chat_model,
    )
    knowledge_base_id = uuid4()

    result = asyncio.run(
        service.answer(
            knowledge_base_id=knowledge_base_id,
            question="What does the policy say?",
            limit=2,
        )
    )

    assert retrieval_service.calls == [
        {
            "knowledge_base_id": knowledge_base_id,
            "question": "What does the policy say?",
            "limit": 2,
        }
    ]
    assert result.answer == "The answer combines two facts [2] and [1]."
    assert [citation.rank for citation in result.citations] == [2, 1]
    assert result.citations[0].filename == "ops.pdf"
    assert result.citations[0].page_number == 2
    assert result.source_chunks == chunks

    prompt = chat_model.calls[0]["user_prompt"]
    system_prompt = chat_model.calls[0]["system_prompt"]
    assert "Do not use outside knowledge" in system_prompt
    assert "Question:\nWhat does the policy say?" in prompt
    assert "[1] filename=policy.pdf" in prompt
    assert f"chunk_id={chunks[0].chunk_id}" in prompt
    assert "[2] filename=ops.pdf" in prompt
    assert "similarity_score=0.9000" in prompt


def test_answer_uses_top_chunk_when_model_omits_citation_markers() -> None:
    chunks = [_result(rank=1), _result(rank=2)]
    service = AnswerService(
        retrieval_service=FakeRetrievalService(chunks),  # type: ignore[arg-type]
        chat_model=FakeChatModel("The answer has no citation marker."),
    )

    result = asyncio.run(service.answer(knowledge_base_id=uuid4(), question="What changed?", limit=2))

    assert len(result.citations) == 1
    assert result.citations[0].chunk_id == chunks[0].chunk_id


def test_answer_allows_calibrated_resume_similarity_scores() -> None:
    resume_score_chunk = _result(rank=1).model_copy(update={"similarity_score": 0.13})
    chat_model = FakeChatModel("Jose is located in Antipolo City, Philippines [1].")
    service = AnswerService(
        retrieval_service=FakeRetrievalService([resume_score_chunk]),  # type: ignore[arg-type]
        chat_model=chat_model,
    )

    result = asyncio.run(service.answer(knowledge_base_id=uuid4(), question="Where is Jose located?", limit=5))

    assert result.answer == "Jose is located in Antipolo City, Philippines [1]."
    assert result.citations[0].chunk_id == resume_score_chunk.chunk_id
    assert len(chat_model.calls) == 1


def test_answer_returns_no_evidence_without_calling_model() -> None:
    chat_model = FakeChatModel()
    service = AnswerService(
        retrieval_service=FakeRetrievalService([]),  # type: ignore[arg-type]
        chat_model=chat_model,
    )

    result = asyncio.run(service.answer(knowledge_base_id=uuid4(), question="What changed?", limit=5))

    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.citations == []
    assert result.source_chunks == []
    assert chat_model.calls == []


def test_answer_returns_no_evidence_for_low_similarity_without_calling_model() -> None:
    low_score_chunk = _result(rank=1).model_copy(update={"similarity_score": 0.01})
    chat_model = FakeChatModel()
    service = AnswerService(
        retrieval_service=FakeRetrievalService([low_score_chunk]),  # type: ignore[arg-type]
        chat_model=chat_model,
    )

    result = asyncio.run(service.answer(knowledge_base_id=uuid4(), question="What changed?", limit=5))

    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.citations == []
    assert result.source_chunks == []
    assert chat_model.calls == []


def test_answer_propagates_provider_error() -> None:
    service = AnswerService(
        retrieval_service=FakeRetrievalService([_result(rank=1)]),  # type: ignore[arg-type]
        chat_model=FailingChatModel(),  # type: ignore[arg-type]
    )

    with pytest.raises(ChatModelError, match="Provider unavailable"):
        asyncio.run(service.answer(knowledge_base_id=uuid4(), question="What changed?", limit=5))
