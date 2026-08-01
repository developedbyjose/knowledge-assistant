from app.rag.providers.local_embedding import LocalEmbeddingProvider


class FakeModel:
    def encode(self, texts, normalize_embeddings, show_progress_bar):  # noqa: ANN001
        return [[0.1] * 384 for _ in texts]


def test_local_embedding_provider_returns_384_dimensions() -> None:
    provider = LocalEmbeddingProvider(model_name="fake")
    provider.__dict__["model"] = FakeModel()

    embedding = provider.embed_query("What is retrieval?")

    assert len(embedding) == 384
