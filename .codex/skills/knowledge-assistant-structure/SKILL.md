---
name: knowledge-assistant-structure
description: Project-local architecture guidance for the Knowledge Assistant monorepo. Use when adding, moving, or reviewing files in this repository, especially frontend routes/components, backend FastAPI modules, RAG ingestion/retrieval/generation/evaluation code, shared API/client types, docs, infrastructure, Docker, environment examples, Makefile tasks, or tests.
---

# Knowledge Assistant Structure

## Overview

Use this skill to keep Knowledge Assistant organized as one product with separate frontend and backend applications. Prefer the existing monorepo boundaries before introducing new top-level folders or cross-app coupling.

## Workflow

1. Inspect the current repository before editing: `find`, `rg --files`, package manifests, test folders, and nearby naming patterns.
2. Place code according to the ownership rules below. If a change spans layers, keep each layer in its proper app or package.
3. Add or update tests in the app/package closest to the changed behavior.
4. Update docs when a change alters architecture, API contracts, retrieval behavior, environment setup, or operating commands.
5. Avoid unrelated restructuring. Preserve user work in the tree.

## Placement Rules

- Put Next.js app router routes and layouts in `apps/web/app/`.
- Put reusable React components in `apps/web/components/`, grouped by `ui`, domain area, or layout role.
- Put frontend feature modules, hooks, browser-side helpers, and frontend tests under `apps/web/features/`, `apps/web/hooks/`, `apps/web/lib/`, and `apps/web/tests/`.
- Put FastAPI routes, configuration, database access, persistence models, schemas, repositories, services, workers, and tests under `apps/api/`.
- Put RAG-specific backend code under `apps/api/app/rag/` by phase: ingestion, retrieval, generation, evaluation, or providers.
- Put generated or handwritten API clients in `packages/api-client/`.
- Put shared TypeScript or schema artifacts that are consumed across apps in `packages/shared-types/`.
- Put durable project knowledge in `docs/`, deployment/runtime files in `infrastructure/`, and root-level orchestration files at the repository root.

## Reference

Read `references/monorepo-structure.md` when a task involves creating directories, deciding where a file belongs, changing architecture, or explaining the repository layout.
