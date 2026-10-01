# Retrieval Evaluation

The first vertical slice proves the retrieval system independently from answer
generation:

1. Upload a text-based PDF or DOCX file.
2. Extract PDF pages with `pypdf`, or DOCX body paragraphs and tables with
   `python-docx` in document order.
3. Clean extracted blocks by removing control characters, repairing hyphenated
   line breaks, and normalizing whitespace.
4. Mark the document as `processing`, then chunk block text with an 800-word
   window and 150-word overlap.
5. Store chunk content with source-specific metadata, word offsets, chunk size,
   overlap, and token count. PDF metadata includes page number; DOCX metadata
   includes paragraph/table block type and block index with no page number.
6. Embed chunks locally with `sentence-transformers/all-MiniLM-L6-v2`.
7. Store 384-dimensional vectors in pgvector.
8. Mark the document as `processed` when indexing succeeds or `failed` with an
   error message when extraction, chunking, embedding, or storage fails.
9. Embed one question and retrieve the top five chunks by cosine distance via
   `POST /api/v1/knowledge-bases/{id}/query-embedding`.
10. Inspect the returned chunks in the Retrieval Lab UI.

LLM answer generation and chat are layered on this retrieval flow, so
representative documents and questions should continue to pass retrieval checks
before evaluating answer quality. Grounded generation skips the chat model when
retrieval returns no chunks or when every retrieved chunk falls below
`RETRIEVAL_MIN_SIMILARITY_SCORE`.

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
  the top result on page 1.
- "What should analysts do before answer generation?" should return
  `onboarding-notes.pdf` in the top result on page 1.
- "Which documents are eligible for vector search results?" should return
  `retrieval-policy.pdf` within the configured top-k window.
- "When should analysts record the first baseline?" should return
  `onboarding-notes.pdf` within the configured top-k window.

Initial metrics live in `app/rag/evaluation`:

- `top_1_accuracy`: fraction of questions where the first retrieved source
  matches the expected filename and page.
- `top_k_hit_rate`: fraction of questions where any source within the requested
  top-k window matches the expected filename and page.

The baseline fixture records each question's expected filename, expected page
number, and expected top-k window. These metrics measure retrieval only; answer
generation quality and citation faithfulness should be evaluated separately
after retrieval passes.

Commands:

```bash
cd apps/api
pytest tests/unit/test_retrieval_baseline_fixtures.py -q
RUN_REAL_RETRIEVAL_BASELINE=1 pytest tests/unit/test_retrieval_baseline_fixtures.py -q
RUN_PGVECTOR_TESTS=1 pytest tests/unit/test_document_repository_vector_search.py -q
```

The first command validates the committed PDF baseline extraction, cleanup,
chunk order, and metadata
without downloading the embedding model. The opt-in real baseline loads the
local sentence-transformers model, and the pgvector check requires a running
database such as `docker compose up -d db` from the repository root.

Known limitations:

- The baseline corpus is intentionally tiny and text-based; it does not measure
  scanned PDFs, tables, multi-column pages, or OCR quality.
- DOCX ingestion covers body paragraphs and tables only. It does not extract
  headers, footers, comments, tracked-change details, images, or OCR text, and
  it cannot provide stable page numbers.
- Chunking still uses word counts as a proxy for tokens.
- Scores are useful for ranking inspection but are not calibrated confidence
  values.
