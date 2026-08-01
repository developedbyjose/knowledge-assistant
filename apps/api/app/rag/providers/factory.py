from app.core.config import settings
from app.rag.providers.chat import ChatModel
from app.rag.providers.embedding import EmbeddingProvider
from app.rag.providers.gemini import GeminiChatModel
from app.rag.providers.local_embedding import LocalEmbeddingProvider


def create_chat_model() -> ChatModel:
    if settings.llm_provider == "gemini":
        return GeminiChatModel(
            api_key=settings.gemini_api_key,
            model=settings.llm_model,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def create_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "local":
        return LocalEmbeddingProvider(model_name=settings.embedding_model)

    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
