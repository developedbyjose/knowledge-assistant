import pytest

from app.core.config import settings
from app.rag.providers.chat import ChatModelError
from app.rag.providers.factory import create_chat_model
from app.rag.providers.gemini import GeminiChatModel


def test_create_chat_model_uses_configured_gemini_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "gemini")
    monkeypatch.setattr(settings, "llm_model", "gemini-flash-lite-latest")
    monkeypatch.setattr(settings, "gemini_api_key", "test-api-key")

    chat_model = create_chat_model()

    assert isinstance(chat_model, GeminiChatModel)
    assert chat_model.model == "gemini-flash-lite-latest"


def test_create_chat_model_requires_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "gemini")
    monkeypatch.setattr(settings, "llm_model", "gemini-flash-lite-latest")
    monkeypatch.setattr(settings, "gemini_api_key", "")

    with pytest.raises(ChatModelError, match="Gemini API key"):
        create_chat_model()


def test_create_chat_model_rejects_unsupported_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "other")

    with pytest.raises(ChatModelError, match="Unsupported LLM provider"):
        create_chat_model()
