# Knowledge Assistant Monorepo Structure

## Canonical Tree

```text
knowledge-assistant/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── chat/
│   │   │   │   ├── documents/
│   │   │   │   ├── knowledge-bases/
│   │   │   │   └── settings/
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── chat/
│   │   │   ├── documents/
│   │   │   └── layout/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── tests/
│   └── api/
│       ├── app/
│       │   ├── api/
│       │   │   └── v1/
│       │   ├── core/
│       │   ├── db/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── repositories/
│       │   ├── services/
│       │   ├── rag/
│       │   │   ├── ingestion/
│       │   │   ├── retrieval/
│       │   │   ├── generation/
│       │   │   ├── evaluation/
│       │   │   └── providers/
│       │   ├── workers/
│       │   └── main.py
│       ├── migrations/
│       └── tests/
├── packages/
│   ├── api-client/
│   └── shared-types/
├── docs/
│   ├── architecture.md
│   ├── decisions/
│   ├── api.md
│   ├── retrieval-evaluation.md
│   └── screenshots/
├── infrastructure/
│   ├── docker/
│   └── scripts/
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

## Ownership

- `apps/web` owns the Next.js user experience: App Router pages, layouts, UI components, browser hooks, frontend utilities, and frontend tests.
- `apps/api` owns the Python backend: FastAPI routes, settings, database integration, domain models, schemas, repository/data-access code, business services, RAG pipeline code, workers, migrations, and backend tests.
- `packages/api-client` owns client code used by the web app or other consumers to call the backend API. Prefer generating it from the backend contract when a generator is present.
- `packages/shared-types` owns shared contracts that must be imported by multiple TypeScript consumers. Do not put backend-only Python schemas here.
- `docs` owns human-readable architecture, decisions, API notes, RAG evaluation methodology, and screenshots.
- `infrastructure` owns Docker-supporting files and operational scripts that are not specific to one app.
- Root files own whole-repo orchestration: Docker Compose, example environment variables, Make tasks, package manager workspace config when present, and the main README.

## Backend Guidelines

- Put route handlers under `apps/api/app/api/v1/`; keep HTTP concerns there and delegate business logic to services.
- Put runtime configuration, security, logging, and app settings under `apps/api/app/core/`.
- Put SQLAlchemy/session/database setup under `apps/api/app/db/`.
- Put persistence models under `apps/api/app/models/` and request/response validation schemas under `apps/api/app/schemas/`.
- Put database query abstractions under `apps/api/app/repositories/`.
- Put application use cases under `apps/api/app/services/`.
- Put background execution entry points under `apps/api/app/workers/`.
- Keep RAG stages isolated:
  - `rag/ingestion` for loading, parsing, chunking, metadata extraction, and indexing.
  - `rag/retrieval` for query rewriting, embedding search, hybrid search, reranking, and context assembly.
  - `rag/generation` for prompt assembly, model calls, citation handling, and answer post-processing.
  - `rag/evaluation` for golden sets, metrics, regression checks, and retrieval/answer quality experiments.
  - `rag/providers` for vector store, embedding, LLM, parser, and storage provider adapters.

## Frontend Guidelines

- Put auth routes under `apps/web/app/(auth)/`.
- Put product routes under `apps/web/app/(dashboard)/`, grouped by dashboard area.
- Use `apps/web/components/ui/` for primitive reusable UI.
- Use `apps/web/components/chat/`, `documents/`, and `layout/` for domain or shell components that are still reusable across pages.
- Use `apps/web/features/` for feature-level orchestration with local components, state, data loading, and actions when a feature grows beyond a single route.
- Use `apps/web/hooks/` for reusable React hooks and `apps/web/lib/` for browser-safe helpers, API wrappers, constants, and formatters.
- Keep route files thin when possible; compose page behavior from components and feature modules.

## Documentation Triggers

Update `docs/architecture.md` when module boundaries, runtime topology, or data flow changes.
Update `docs/api.md` when endpoint contracts, authentication, or API error behavior changes.
Update `docs/retrieval-evaluation.md` when ingestion, retrieval, ranking, generation, citation, or evaluation behavior changes.
Add a decision record in `docs/decisions/` when choosing a durable architecture, vendor, database, queue, vector store, model provider, or cross-app contract.
