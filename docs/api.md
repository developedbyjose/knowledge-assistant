# Knowledge Assistant API

The product API supports retrieval validation and cited answer generation. All
product endpoints are versioned under `/api/v1`.

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

## Answers

- `POST /api/v1/knowledge-bases/{id}/answers` accepts
  `{ "question": "...", "limit": 5 }`, retrieves the top matching chunks, calls
  the configured chat model, and returns a grounded answer with citations and
  source chunks.
- The response includes `question`, `answer`, `citations`, and `source_chunks`.
  Each citation points back to a retrieved chunk with chunk/document IDs,
  filename, page number, chunk index, and retrieval rank.
- When retrieval returns no chunks, or all retrieved chunks are below
  `RETRIEVAL_MIN_SIMILARITY_SCORE`, the API returns a graceful no-evidence
  answer without calling the chat model.

Answer generation currently uses `LLM_PROVIDER=gemini` with
`LLM_MODEL=gemini-flash-lite-latest`. Missing, unavailable, quota-limited, or
failed chat-provider calls return `502`.

## Conversations

- `POST /api/v1/conversations` accepts `knowledge_base_id` and optional `title`,
  creates a chat thread, and returns it with an empty `messages` list.
- `GET /api/v1/conversations` lists chat threads with ordered messages.
- `GET /api/v1/conversations/{id}` returns one chat thread with ordered
  messages. Assistant messages include persisted `citations`, `source_chunks`,
  and optional `feedback_rating`.
- `DELETE /api/v1/conversations/{id}` deletes a chat thread and its messages.
  Successful deletes return `204`.
- `POST /api/v1/conversations/{id}/messages` accepts
  `{ "content": "...", "limit": 5, "stream": false }`, persists the user
  message, retrieves grounded context from the conversation knowledge base,
  persists the assistant response, and returns citations plus source chunks.
- Assistant response citations are persisted as message-to-chunk mappings. Each
  cited source includes document ID, filename, page number, chunk index,
  retrieval rank, similarity score, and source preview text so reopened
  conversations can show the same evidence.
- The same message endpoint streams with Server-Sent Events when `stream` is
  true or the request `Accept` header includes `text/event-stream`.

Streaming events are `message_start`, `token`, `sources`, `message_done`, and
`error`. Route handlers only format HTTP/SSE responses; retrieval, prompt
assembly, generation, and persistence stay in the service layer.

## Feedback

- `POST /api/v1/messages/{id}/feedback` accepts
  `{ "rating": "positive" }` or `{ "rating": "negative" }` for assistant
  messages.
- The response includes feedback `id`, `message_id`, `rating`, and `created_at`.
- Missing messages return `404`; feedback on user/system messages returns
  `400`; invalid ratings return `422`.

Missing knowledge bases or documents return `404`.
