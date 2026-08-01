# Architecture

Knowledge Assistant is split into a FastAPI backend in `apps/api` and a Next.js
frontend in `apps/web`.

## First Vertical Slice

The initial backend follows a thin-route architecture:

API routes call application services, services orchestrate repositories and RAG
providers, and repositories own SQLAlchemy persistence. RAG-specific code is
split by phase under `app/rag`.

The current persistence milestone includes only:

- `knowledge_bases`
- `documents`
- `document_chunks`

The frontend currently exposes a focused Retrieval Lab instead of a chat UI so
retrieval quality can be validated before an LLM is connected.
