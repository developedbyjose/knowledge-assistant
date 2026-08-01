# Retrieval Evaluation

The first vertical slice proves the retrieval system independently from answer
generation:

1. Upload a text-based PDF.
2. Extract text with `pypdf`.
3. Clean extracted pages by removing control characters, repairing hyphenated
   line breaks, and normalizing whitespace.
4. Mark the document as `processing`, then chunk page text with an 800-word
   window and 150-word overlap.
5. Store chunk content with metadata including source type, page number, word
   offsets, chunk size, overlap, and token count.
6. Embed chunks locally with `sentence-transformers/all-MiniLM-L6-v2`.
7. Store 384-dimensional vectors in pgvector.
8. Mark the document as `processed` when indexing succeeds or `failed` with an
   error message when extraction, chunking, embedding, or storage fails.
9. Embed one question and retrieve the top five chunks by cosine distance via
   `POST /api/v1/knowledge-bases/{id}/query-embedding`.
10. Inspect the returned chunks in the Retrieval Lab UI.

LLM answer generation is layered on this retrieval flow, so representative PDFs
and questions should continue to pass retrieval checks before evaluating answer
quality.

## First Baseline

Committed fixtures live in `apps/api/tests/fixtures/retrieval/`:

- `retrieval-policy.pdf`: query-embedding policy, processed-document filtering,
  and vector ranking language.
- `onboarding-notes.pdf`: Retrieval Lab analyst workflow and baseline-recording
  language.
- `baseline.json`: expected phrases, chunk settings, embedding model, and
  representative queries.

Baseline settings:

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector dimensions: `384`
- Chunk size: `800` words
- Chunk overlap: `150` words
- Retrieval limit: top `5`

Representative checks:

- "How are query embeddings ranked?" should return `retrieval-policy.pdf` in
  the top result.
- "What should analysts do before answer generation?" should return
  `onboarding-notes.pdf` in the top result.

Commands:

```bash
cd apps/api
pytest tests/unit/test_retrieval_baseline_fixtures.py -q
RUN_REAL_RETRIEVAL_BASELINE=1 pytest tests/unit/test_retrieval_baseline_fixtures.py -q
RUN_PGVECTOR_TESTS=1 pytest tests/unit/test_document_repository_vector_search.py -q
```

The first command validates PDF extraction, cleanup, chunk order, and metadata
without downloading the embedding model. The opt-in real baseline loads the
local sentence-transformers model, and the pgvector check requires a running
database such as `docker compose up -d db` from the repository root.

Known limitations:

- The baseline corpus is intentionally tiny and text-based; it does not measure
  scanned PDFs, tables, multi-column pages, or OCR quality.
- Chunking still uses word counts as a proxy for tokens.
- Scores are useful for ranking inspection but are not calibrated confidence
  values.
