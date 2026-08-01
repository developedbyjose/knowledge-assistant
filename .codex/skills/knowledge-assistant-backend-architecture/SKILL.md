---
name: knowledge-assistant-backend-architecture
description: Project-local backend architecture guidance for the Knowledge Assistant API. Use when adding, editing, moving, or reviewing FastAPI routes, application services, repositories, AI providers, storage providers, vector search, RAG ingestion/retrieval/generation code, persistence models, backend tests, or backend architecture docs in this repository.
---

# Knowledge Assistant Backend Architecture

## Overview

Use a pragmatic layered architecture for the Knowledge Assistant backend. Keep HTTP concerns, use-case orchestration, persistence, and third-party integrations in separate layers so RAG logic remains testable and replaceable.

## Layer Flow

API Route
-> Application Service
-> Repository / AI Provider / Storage Provider
-> Database or External Service

Dependencies point inward through interfaces or narrow constructor-injected collaborators. Avoid route handlers importing concrete database clients, SDK clients, embedding models, chat models, parsers, object storage clients, or vector search SDKs directly.

## API Layer

Use API routes for:

- HTTP request handling
- Request and response schemas
- Input validation
- Authentication and authorization dependencies
- Response formatting
- Status codes and FastAPI exceptions

Do not put chunking, embedding, retrieval, prompt construction, model calls, storage uploads, or database transaction logic in API route handlers. A route should validate inputs, call an application service, and map service results or domain errors to HTTP responses.

## Service Layer

Use application services for product use cases, including:

- Upload document
- Process document
- Ask question
- Create knowledge base
- Delete document
- Record feedback

Services orchestrate repositories and providers. They may coordinate transactions, enforce business rules, decide workflow order, normalize domain errors, and assemble results for the API layer. Keep services free of FastAPI request objects, response objects, dependency decorators, and route-specific status-code decisions.

## Repository Layer

Use repositories for persistence only. Prefer explicit repository classes or protocols for:

- `DocumentRepository`
- `ChunkRepository`
- `ConversationRepository`
- `KnowledgeBaseRepository`

Repositories should hide database details from services. They can create queries, map database rows or ORM models to domain/data-transfer objects, and handle persistence-specific errors. They should not call LLMs, compute embeddings, parse documents, perform chunking, or format HTTP responses.

## Provider Layer

Use providers to isolate third-party or replaceable infrastructure:

- `EmbeddingProvider`
- `ChatModelProvider`
- `DocumentParser`
- `ObjectStorage`
- `VectorSearchProvider`

Provider implementations may depend on external SDKs or services such as OpenAI, Gemini, object storage, document parsing libraries, or vector databases. Services should depend on provider interfaces, not directly on vendor SDKs, so local tests can use fakes.

## Implementation Rules

- Place backend code under `apps/api/` and follow nearby naming patterns before introducing new directories.
- Prefer one service per cohesive use-case area, not one service per helper function.
- Keep route modules thin enough to read as HTTP adapters.
- Keep RAG details behind services and providers: document parsing, chunking, embedding, retrieval, prompt assembly, generation, citation assembly, and evaluation logic should not leak into routes.
- Use dependency injection or factory functions to assemble concrete repositories and providers at the application boundary.
- Add focused tests at the layer where behavior lives: route tests for HTTP behavior, service tests for use-case orchestration, repository tests for persistence queries, and provider tests or contract tests for adapters.
- If existing code violates this layering, improve only the touched path unless the user asks for a broader refactor.

When this skill and `knowledge-assistant-structure` both apply, use this skill for backend layer responsibilities and use `knowledge-assistant-structure` for monorepo placement.
