import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.schemas.retrieval import RetrievalResult, RetrievalResults
from app.services.conversation_service import ConversationService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def refresh(self, _obj) -> None:  # noqa: ANN001
        return None


class FakeConversationRepository:
    def __init__(self, conversation) -> None:  # noqa: ANN001
        self.conversation = conversation
        self.messages = conversation.messages

    def get(self, conversation_id: UUID):  # noqa: ANN201
        if conversation_id != self.conversation.id:
            return None
        return self.conversation

    def add_message(self, *, conversation, role, content, model_name=None):  # noqa: ANN001, ANN201
        message = SimpleNamespace(
            id=uuid4(),
            conversation_id=conversation.id,
            role=role,
            content=content,
            model_name=model_name,
            created_at=datetime.now(timezone.utc),
        )
        conversation.messages.append(message)
        return message


class FakeRetrievalService:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self.results = results
        self.calls = []

    def retrieve(self, *, knowledge_base_id, question, limit):  # noqa: ANN001, ANN201
        self.calls.append((knowledge_base_id, question, limit))
        return RetrievalResults(question=question, results=self.results)


class FakeChatModel:
    def __init__(self, answer: str = "Grounded answer [1].") -> None:
        self.answer = answer
        self.generate_calls = []
        self.stream_calls = []

    async def generate(self, *, system_prompt, user_prompt):  # noqa: ANN001, ANN201
        self.generate_calls.append((system_prompt, user_prompt))
        return self.answer

    async def stream_generate(self, *, system_prompt, user_prompt):  # noqa: ANN001, ANN201
        self.stream_calls.append((system_prompt, user_prompt))
        for token in ["Grounded ", "answer [1]."]:
            yield token


def _conversation():
    return SimpleNamespace(
        id=uuid4(),
        user_id=None,
        knowledge_base_id=uuid4(),
        title="New chat",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        messages=[],
    )


def _result(rank: int = 1) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="policy.pdf",
        rank=rank,
        similarity_score=0.9,
        content="Policy evidence.",
        page_number=1,
        chunk_index=0,
        metadata={"page_number": 1},
    )


def _service(*, chunks: list[RetrievalResult], chat_model=None):  # noqa: ANN001, ANN201
    conversation = _conversation()
    session = FakeSession()
    service = ConversationService(
        session=session,  # type: ignore[arg-type]
        retrieval_service=FakeRetrievalService(chunks),  # type: ignore[arg-type]
        chat_model=chat_model or FakeChatModel(),  # type: ignore[arg-type]
    )
    service.conversations = FakeConversationRepository(conversation)  # type: ignore[assignment]
    return service, conversation, session


def test_add_message_persists_user_and_assistant_messages() -> None:
    service, conversation, session = _service(chunks=[_result()])

    response = asyncio.run(
        service.add_message(conversation_id=conversation.id, content="What changed?", limit=5)
    )

    assert session.commits == 1
    assert [message.role for message in conversation.messages] == ["user", "assistant"]
    assert response.assistant_message.content == "Grounded answer [1]."
    assert response.citations[0].filename == "policy.pdf"
    assert response.source_chunks[0].content == "Policy evidence."


def test_add_message_skips_model_when_context_is_insufficient() -> None:
    chat_model = FakeChatModel()
    low_score = _result().model_copy(update={"similarity_score": 0.01})
    service, conversation, _session = _service(chunks=[low_score], chat_model=chat_model)

    response = asyncio.run(
        service.add_message(conversation_id=conversation.id, content="What changed?", limit=5)
    )

    assert chat_model.generate_calls == []
    assert response.citations == []
    assert response.source_chunks == []
    assert "could not find enough relevant evidence" in response.assistant_message.content


def test_stream_message_emits_tokens_sources_and_done() -> None:
    service, conversation, session = _service(chunks=[_result()])

    async def collect():
        return [
            event
            async for event in service.stream_message(
                conversation_id=conversation.id,
                content="What changed?",
                limit=5,
            )
        ]

    events = asyncio.run(collect())

    assert [event["event"] for event in events] == [
        "message_start",
        "token",
        "token",
        "sources",
        "message_done",
    ]
    assert session.commits == 1
    assert conversation.messages[-1].content == "Grounded answer [1]."
