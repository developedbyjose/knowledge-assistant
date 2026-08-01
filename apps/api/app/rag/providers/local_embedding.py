from __future__ import annotations

from functools import cached_property

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.rag.providers.embedding import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, *, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model

    @cached_property
    def model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()

        return [list(embedding) for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
