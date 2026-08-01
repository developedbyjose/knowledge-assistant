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
- `conversations`
- `messages`

Document ingestion is synchronous for the first slice. Upload and reprocess
commands create or reuse a document record, transition it through
`pending -> processing -> processed` or `failed`, extract and clean PDF page
text, chunk pages with source metadata, generate local embeddings, and store the
chunk vectors in pgvector.

The backend now layers cited answer generation and chat on top of retrieval.
Answer and conversation routes call application services, services retrieve
source chunks and assemble grounded prompts, and the Gemini chat provider
remains behind the model-provider interface. Conversations persist ordered user
and assistant messages; citations and source chunks are returned in responses
without a separate citation table in this milestone.

The frontend keeps the focused Retrieval Lab UI and adds `/chat` as the primary
assistant workflow. The chat page uses Server-Sent Events for one-way assistant
streaming, shows loading/error/insufficient-context states, and keeps source
evidence visible beside the transcript.
