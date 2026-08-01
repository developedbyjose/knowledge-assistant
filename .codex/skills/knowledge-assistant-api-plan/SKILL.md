---
name: knowledge-assistant-api-plan
description: "Project-local API plan guidance for Knowledge Assistant. Use when adding, editing, or reviewing FastAPI routes, API schemas, endpoint tests, frontend API clients, API docs, auth endpoints, knowledge base/document/conversation/message/feedback routes, or streaming message behavior under versioned /api/v1 endpoints."
---

# Knowledge Assistant API Plan

## Overview

Use this skill to keep the Knowledge Assistant HTTP API consistent, versioned, and easy for the frontend to consume. Prefer `/api/v1` for all product endpoints and keep route handlers as thin HTTP adapters over application services.

When this skill overlaps with `knowledge-assistant-backend-architecture`, use that skill for route/service/repository/provider boundaries and this skill for endpoint shape, route grouping, and streaming behavior.

## Versioning

- Use versioned endpoints under `/api/v1`.
- Do not add unversioned product routes except redirects or compatibility shims requested by the user.
- Keep route names resource-oriented and stable for generated or handwritten clients.
- Preserve the route contract below unless the user explicitly changes the API plan.

## Endpoint Contract

### Health

- `GET /api/v1/health`

Use health for lightweight service status. Keep it cheap and independent of heavyweight model calls.

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Use these endpoints for account creation, session/token creation, and current-user inspection. If auth is not in the current milestone, keep protected route dependencies easy to add later instead of baking anonymous behavior deeply into services.

### Knowledge Bases

- `GET /api/v1/knowledge-bases`
- `POST /api/v1/knowledge-bases`
- `GET /api/v1/knowledge-bases/{id}`
- `PATCH /api/v1/knowledge-bases/{id}`
- `DELETE /api/v1/knowledge-bases/{id}`

Use collection routes for listing and creation. Use item routes for read, partial update, and deletion. Keep naming aligned with the database table `knowledge_bases` while exposing hyphenated URLs.

### Documents

- `POST /api/v1/knowledge-bases/{id}/documents`
- `GET /api/v1/knowledge-bases/{id}/documents`
- `GET /api/v1/documents/{id}`
- `DELETE /api/v1/documents/{id}`
- `POST /api/v1/documents/{id}/reprocess`

Use nested knowledge-base document routes when the knowledge base is part of the command or list scope. Use top-level document routes when addressing a document directly. Model upload and reprocess as commands that delegate parsing, storage, chunking, and embedding work to services/providers.

### Conversations

- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `GET /api/v1/conversations/{id}`
- `POST /api/v1/conversations/{id}/messages`

Create conversations independently from messages so the UI can start a thread before or during the first question. Add messages through the conversation route because message creation depends on conversation context and, for assistant responses, retrieval/generation orchestration.

### Feedback

- `POST /api/v1/messages/{id}/feedback`

Attach feedback to a message, typically an assistant message. Keep feedback creation separate from message creation so users can rate or comment after reading a response.

## Streaming

Use Server-Sent Events for streaming messages initially. SSE is the preferred first implementation for one-directional assistant token streaming because it is simpler than full WebSocket communication.

Implementation guidance:

- Keep `POST /api/v1/conversations/{id}/messages` as the message creation entry point.
- Support streaming with an explicit request option, response media type, or nearby route pattern that matches existing code conventions.
- Emit incremental assistant content as SSE events and finish with a terminal event that lets the client close cleanly.
- Persist the user message and final assistant message through the service layer; do not make route handlers assemble prompts, perform retrieval, or call chat providers directly.
- Use WebSockets only after there is a clear bidirectional requirement, such as collaborative presence, cancellation protocols that cannot fit HTTP/SSE, or live multi-client chat state.

## Implementation Rules

- Place FastAPI route modules under `apps/api/` according to nearby naming patterns.
- Keep endpoint handlers responsible for HTTP concerns: request parsing, auth dependencies, response schemas, status codes, and error mapping.
- Put business workflows in application services, including document upload/reprocess, conversation creation, message generation, citation assembly, and feedback recording.
- Add route tests for status codes, request/response shapes, auth behavior, and SSE framing when streaming is implemented.
- Update API client types or docs when endpoint paths, payloads, response schemas, or streaming semantics change.
