# Knowledge Assistant API

The first product API validates retrieval before LLM generation. All product
endpoints are versioned under `/api/v1`.

## Knowledge Bases

- `GET /api/v1/health` returns lightweight service status.
- `GET /api/v1/knowledge-bases` lists retrieval collections.
- `POST /api/v1/knowledge-bases` creates a collection.
- `GET /api/v1/knowledge-bases/{id}` returns one collection with document and
  chunk counts.
- `PATCH /api/v1/knowledge-bases/{id}` updates `name` and/or `description`.
  Empty update payloads return `400`.
- `DELETE /api/v1/knowledge-bases/{id}` deletes the collection and cascades its
  documents and chunks. Successful deletes return `204`.

## Documents

- `POST /api/v1/knowledge-bases/{id}/documents` accepts one PDF as multipart
  field `file`, extracts text, chunks it, embeds it, and stores chunks in
  pgvector synchronously. Uploads are stored under `UPLOAD_DIR`, must use a PDF
  filename/content type, cannot be empty, must start with a PDF signature, and
  are capped by `MAX_UPLOAD_BYTES` (`26214400` by default).
- `GET /api/v1/knowledge-bases/{id}/documents` lists documents in a collection.
- `GET /api/v1/documents/{id}` returns one document with status, page count, and
  chunk count.
- `DELETE /api/v1/documents/{id}` deletes the document, chunks, and local stored
  file when present. Successful deletes return `204`.
- `POST /api/v1/documents/{id}/reprocess` re-parses the stored PDF, replaces
  chunks, recomputes embeddings, and returns the updated document.

## Retrieval

- `POST /api/v1/knowledge-bases/{id}/query-embedding` accepts
  `{ "question": "...", "limit": 5 }`, embeds the question with the configured
  embedding provider, and returns the top matching chunks. Each result includes
  rank, similarity score, source document IDs, filename, page number, chunk
  index, content, and chunk metadata.
- `POST /api/v1/knowledge-bases/{id}/retrieval-query` remains available as a
  compatibility alias for the same behavior.

Retrieval returns `400` if the selected knowledge base was indexed with a
different embedding model than the current runtime configuration or if the
query embedding dimension does not match the configured vector size.

This milestone intentionally does not call Gemini or any other chat model.
Missing knowledge bases or documents return `404`.
