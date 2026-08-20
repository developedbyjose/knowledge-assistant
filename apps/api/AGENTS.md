# API Agent

Follow these instructions for all work under `apps/api`.

## Folder Structure

- `app/api/v1/`: FastAPI route modules, dependency functions, HTTP status
  mapping, request parsing, and response formatting.
- `app/core/`: runtime settings, security helpers, logging, CORS, and app-level
  configuration.
- `app/db/`: SQLAlchemy engine, sessions, metadata, and database setup.
- `app/models/`: persistence models only.
- `app/schemas/`: request and response validation schemas.
- `app/repositories/`: database query abstractions and persistence mapping.
- `app/services/`: application use cases and business workflow orchestration.
- `app/rag/ingestion/`: document parsing, cleaning, chunking, and indexing
  preparation.
- `app/rag/retrieval/`: embedding search, ranking, filtering, and context
  assembly.
- `app/rag/generation/`: prompt assembly, answer generation, and citation
  handling.
- `app/rag/evaluation/`: fixtures, metrics, and retrieval or answer quality
  regression checks.
- `app/rag/providers/`: replaceable providers for embeddings, chat models,
  parsers, vector stores, and external services.
- `migrations/`: Alembic migrations.
- `tests/`: route, unit, repository, service, provider, and integration tests.

## Architecture Rules

- Keep route handlers as HTTP adapters. They should validate input, call an
  application service, and translate domain errors to HTTP responses.
- Put business logic in services, not route modules or repositories.
- Keep repositories focused on persistence. They must not call LLMs, parse
  documents, compute embeddings, or format HTTP responses.
- Keep provider SDK usage behind provider interfaces or factories so tests can
  use fakes.
- Keep RAG details out of route handlers. Parsing, chunking, embedding,
  retrieval, prompt construction, model calls, and citation assembly belong in
  services or RAG modules.
- Use `/api/v1` for product endpoints. Do not add unversioned product routes
  unless they are explicit compatibility shims.

## Security Rules

- Treat every request body, path parameter, query parameter, uploaded file, and
  document chunk as untrusted input.
- Enforce authentication and authorization in dependencies or service
  boundaries before accessing tenant, workspace, knowledge-base, document,
  conversation, message, or feedback records.
- Avoid leaking whether another user's resource exists. Prefer authorization
  checks that return a safe `404` or `403` consistently with existing route
  behavior.
- Restrict uploads by content type, size, page count, and parser capability
  before processing.
- Do not execute uploaded files or extracted text. Do not pass user-controlled
  values into shell commands.
- Use parameterized SQLAlchemy queries. Never build SQL with string
  interpolation from request data.
- Do not log API keys, auth headers, session tokens, raw provider responses with
  secrets, or full private document contents.
- Keep CORS allowlists explicit in production settings.
- Read configuration from environment-backed settings. Do not hard-code
  credentials, provider keys, database URLs, or private endpoints.
- Add or update `.env.example` when a new setting is required, using placeholder
  values only.

## Testing Expectations

- Add route tests for status codes, auth behavior, request validation, response
  shapes, and streaming framing when endpoint behavior changes.
- Add service tests for use-case workflow decisions and domain errors.
- Add repository tests for persistence queries, ownership filtering, and vector
  search behavior.
- Add provider tests or fakes for external model, embedding, parser, or storage
  adapters.
