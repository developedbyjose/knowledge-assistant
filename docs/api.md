# Knowledge Assistant API

The first product API validates retrieval before LLM generation. All product
endpoints are versioned under `/api/v1`.

## Retrieval Slice

- `GET /api/v1/health` returns lightweight service status.
- `GET /api/v1/knowledge-bases` lists retrieval collections.
- `POST /api/v1/knowledge-bases` creates a collection.
- `POST /api/v1/knowledge-bases/{id}/documents` accepts one PDF as multipart
  field `file`, extracts text, chunks it, embeds it, and stores chunks in
  pgvector synchronously.
- `POST /api/v1/knowledge-bases/{id}/retrieval-query` accepts
  `{ "question": "...", "limit": 5 }` and returns the top matching chunks.

This milestone intentionally does not call Gemini or any other chat model.
