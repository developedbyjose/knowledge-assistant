# Knowledge Assistant API

The product API supports retrieval validation and cited answer generation. All
product endpoints are versioned under `/api/v1`.

## Authentication and roles

Browser authentication uses an opaque token in an HTTP-only, SameSite=Lax
cookie. Only a SHA-256 hash of the token is stored in `auth_sessions`; sessions
expire after seven days by default. Unsafe cookie-authenticated requests from
an origin outside `CORS_ORIGINS` are rejected.

- `POST /api/v1/auth/login` creates a session from `email` and `password`.
- `POST /api/v1/auth/logout` revokes the session and clears its cookie.
- `GET /api/v1/auth/me` returns the current account and role.
- `POST /api/v1/auth/change-password` replaces a temporary password, revokes
  prior sessions, and rotates the current session.
- `GET/POST /api/v1/users`, `GET/PATCH /api/v1/users/{id}`, and
  `POST /api/v1/users/{id}/reset-password` are superadmin-only.

Health and login are public; all other product routes require authentication.
Temporary-password accounts can access only auth endpoints. Normal users can
use owner-scoped chat against active knowledge bases. Admins can also manage
knowledge bases, documents, and retrieval operations. Superadmins additionally
manage accounts. There is no public registration endpoint.

## Knowledge Bases

Knowledge bases expose `is_active`. Normal users see active bases only. Admins
can activate or deactivate bases; inactive bases preserve history but reject
new conversations and messages.

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

- `POST /api/v1/knowledge-bases/{id}/documents` accepts one text-based PDF or
  DOCX as multipart field `file`, extracts text, chunks it, embeds it, and
  stores chunks in pgvector synchronously. Uploads are stored under
  `UPLOAD_DIR`, cannot be empty, and are capped by `MAX_UPLOAD_BYTES`
  (`26214400` by default). PDF signatures and DOCX Office ZIP structure must
  match the filename and declared MIME type; generic `application/octet-stream`
  is accepted only when those checks pass. Encrypted and corrupt DOCX archives
  are rejected, and their total expanded size is capped by
  `MAX_DOCX_UNCOMPRESSED_BYTES` (`104857600` by default).
- `GET /api/v1/knowledge-bases/{id}/documents` lists documents in a collection.
- `GET /api/v1/documents/{id}` returns one document with status, page count, and
  chunk count.
- `GET /api/v1/documents/{id}/content` returns the original stored file. The
  optional `disposition=inline|attachment` query controls `Content-Disposition`
  and defaults to `inline`. Responses use the stored MIME type and original
  filename, disable shared caching, and prevent MIME sniffing.
  - Normal users can access files only from active knowledge bases available to
    chat. Admins and superadmins can also access files from inactive knowledge
    bases.
  - Inaccessible documents, missing database records, missing stored files, and
    unsafe storage paths all return the same `404` response.
- `DELETE /api/v1/documents/{id}` deletes the document, chunks, and local stored
  file when present. Successful deletes return `204`.
- `POST /api/v1/documents/{id}/reprocess` selects the parser from the stored
  canonical MIME type, replaces chunks, recomputes embeddings, and returns the
  updated document.

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
  filename, optional page number, chunk index, and retrieval rank. DOCX chunks
  have no page number because Word pagination depends on the renderer.
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

Conversations and feedback are owner-only for every role. Cross-user access
returns `404`. Ownership and active-base validation run before SSE headers are
sent, so denied streams return an ordinary HTTP error.

## Feedback

- `POST /api/v1/messages/{id}/feedback` accepts
  `{ "rating": "positive" }` or `{ "rating": "negative" }` for assistant
  messages.
- The response includes feedback `id`, `message_id`, `rating`, and `created_at`.
- Missing messages return `404`; feedback on user/system messages returns
  `400`; invalid ratings return `422`.

Missing knowledge bases or documents return `404`.
