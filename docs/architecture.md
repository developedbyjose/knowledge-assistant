# Architecture

Knowledge Assistant is split into a FastAPI backend in `apps/api` and a Next.js
frontend in `apps/web`.

## First Vertical Slice

The initial backend follows a thin-route architecture:

API routes call application services, services orchestrate repositories and RAG
providers, and repositories own SQLAlchemy persistence. RAG-specific code is
split by phase under `app/rag`.

The current persistence model includes:

- `knowledge_bases`
- `documents`
- `document_chunks`
- `conversations`
- `messages`
- `message_citations`
- `message_feedback`
- `users`
- `auth_sessions`

Document ingestion is synchronous for the first slice. Upload and reprocess
commands create or reuse a document record, transition it through
`pending -> processing -> processed` or `failed`, extract and clean PDF page
text, chunk pages with source metadata, generate local embeddings, and store the
chunk vectors in pgvector.

The backend now layers cited answer generation and chat on top of retrieval.
Answer and conversation routes call application services, services retrieve
source chunks and assemble grounded prompts, and the Gemini chat provider
remains behind the model-provider interface. Conversations persist ordered user
and assistant messages. Assistant citations are now persisted in
`message_citations` as message-to-chunk mappings, and thumbs feedback is stored
in `message_feedback`.

The frontend keeps the focused Retrieval Lab UI and adds `/chat` as the primary
assistant workflow. The chat page uses Server-Sent Events for one-way assistant
streaming, shows loading/error/insufficient-context states, keeps source
evidence visible beside the transcript, restores sources when conversations are
reopened, and records assistant response feedback.

## Authentication and authorization

`users` stores normalized email identities, Argon2 password hashes, the
`superadmin`/`admin`/`user` role, active status, and the mandatory-password-
change state. `auth_sessions` stores only SHA-256 hashes of random opaque tokens
plus expiry timestamps; browsers receive the raw token in an HTTP-only,
SameSite=Lax cookie.

FastAPI dependencies authenticate protected requests and enforce roles before
application services run. Knowledge and PDF mutation requires admin access;
account management requires superadmin access. Conversation repositories always
filter by the current user's ID, including for admins, and new messages require
an active knowledge base.

The frontend mirrors these boundaries for navigation: `/login` establishes a
session, `/change-password` handles temporary credentials, `/chat` is shared by
all roles, `/` is the admin knowledge-management workspace, and `/users` is
superadmin-only.

After migrating the database, create the initial superadmin from `apps/api`:

```bash
python -m app.cli.create_superadmin
```

Production must use `SESSION_COOKIE_SECURE=true`, HTTPS, and exact frontend
origins in `CORS_ORIGINS`. PDF remains the only supported ingestion format.

## Developer Operations

See [Running and Accessing the Database](database.md) for the essential Docker
Compose commands, migrations, PostgreSQL access, connection settings, and local
troubleshooting.
