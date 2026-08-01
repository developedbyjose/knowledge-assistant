from __future__ import annotations

import json
import math
import os
from pathlib import Path

import pytest

from app.rag.ingestion.chunker import TextChunker
from app.rag.ingestion.pdf_parser import PdfParser
from app.rag.evaluation.metrics import EvaluationCaseResult, top_1_accuracy, top_k_hit_rate
from app.rag.providers.local_embedding import LocalEmbeddingProvider

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "retrieval"
BASELINE = json.loads((FIXTURE_DIR / "baseline.json").read_text())


def test_baseline_pdfs_extract_expected_text_and_chunk_metadata() -> None:
    parser = PdfParser()
    chunker = TextChunker(chunk_size=800, overlap=150)

    for document in BASELINE["documents"]:
        pages = parser.parse(FIXTURE_DIR / document["filename"])
        chunks = chunker.chunk_pages(pages)

        assert len(pages) == 1
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].page_number == 1
        assert chunks[0].metadata["source"] == "pdf"
        assert chunks[0].metadata["page_number"] == 1
        for phrase in document["expected_phrases"]:
            assert phrase in chunks[0].content


def test_baseline_queries_define_document_page_and_top_k_expectations() -> None:
    assert len(BASELINE["queries"]) >= 4
    for query in BASELINE["queries"]:
        assert query["question"]
        assert query["expected_filename"] in {
            document["filename"] for document in BASELINE["documents"]
        }
        assert query["expected_page_number"] == 1
        assert query["expected_top_k"] >= 1


def test_retrieval_evaluation_metrics_measure_top_1_and_top_k_hits() -> None:
    results = [
        EvaluationCaseResult(
            question="How are query embeddings ranked?",
            expected_filename="retrieval-policy.pdf",
            expected_page_number=1,
            retrieved=[
                {"filename": "retrieval-policy.pdf", "page_number": 1},
                {"filename": "onboarding-notes.pdf", "page_number": 1},
            ],
        ),
        EvaluationCaseResult(
            question="When should analysts record the baseline?",
            expected_filename="onboarding-notes.pdf",
            expected_page_number=1,
            retrieved=[
                {"filename": "retrieval-policy.pdf", "page_number": 1},
                {"filename": "onboarding-notes.pdf", "page_number": 1},
            ],
        ),
    ]

    assert top_1_accuracy(results) == 0.5
    assert top_k_hit_rate(results, k=2) == 1.0


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_RETRIEVAL_BASELINE") != "1",
    reason="Set RUN_REAL_RETRIEVAL_BASELINE=1 to run the local sentence-transformers baseline.",
)
def test_real_embedding_baseline_returns_expected_documents() -> None:
    parser = PdfParser()
    chunker = TextChunker(chunk_size=800, overlap=150)
    provider = LocalEmbeddingProvider(model_name=BASELINE["embedding_model"])
    chunks = []

    for document in BASELINE["documents"]:
        pages = parser.parse(FIXTURE_DIR / document["filename"])
        for chunk in chunker.chunk_pages(pages):
            chunks.append(
                {
                    "filename": document["filename"],
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "embedding": provider.embed_texts([chunk.content])[0],
                }
            )

    for query in BASELINE["queries"]:
        query_embedding = provider.embed_query(query["question"])
        ranked = sorted(
            chunks,
            key=lambda chunk: _cosine_similarity(query_embedding, chunk["embedding"]),
            reverse=True,
        )

        assert ranked[0]["filename"] == query["expected_filename"]
        assert ranked[0]["page_number"] == query["expected_page_number"]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return numerator / (left_norm * right_norm)
