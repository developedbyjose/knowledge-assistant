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

Document ingestion is synchronous for the first slice. Upload and reprocess
commands create or reuse a document record, transition it through
`pending -> processing -> processed` or `failed`, extract and clean PDF page
text, chunk pages with source metadata, generate local embeddings, and store the
chunk vectors in pgvector.

The backend now layers cited answer generation on top of retrieval. Answer
routes call an application service, the service retrieves source chunks, and the
Gemini chat provider remains behind the model-provider interface. The frontend
still exposes a focused Retrieval Lab UI, with client support for the cited
answer endpoint available for the next UI slice.
