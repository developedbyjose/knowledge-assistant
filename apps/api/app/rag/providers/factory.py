from app.core.config import settings
from app.rag.providers.chat import ChatModel
from app.rag.providers.gemini import GeminiChatModel


def create_chat_model() -> ChatModel:
    if settings.llm_provider == "gemini":
        return GeminiChatModel(
            api_key=settings.gemini_api_key,
            model=settings.llm_model,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
