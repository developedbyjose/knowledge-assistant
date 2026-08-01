---
name: knowledge-assistant-initial-database-design
description: "Project-local initial database design guidance for Knowledge Assistant. Use when adding, editing, or reviewing database migrations, persistence models, repositories, seed data, backend schemas, tests, or docs for the first milestone tables: knowledge_bases, documents, document_chunks, conversations, and messages; also use when planning later user, workspace, citation, or feedback tables."
---

# Knowledge Assistant Initial Database Design

## Overview

Use this skill to keep the first database milestone aligned with the product's RAG flow: create knowledge bases, upload/process documents into chunks, and store conversations with messages. Treat the full schema below as the intended direction, but implement only the milestone tables unless the user explicitly expands scope.

When this skill overlaps with `knowledge-assistant-backend-architecture`, use that skill for backend layering and this skill for table shape, relationships, and milestone scope.

## First Milestone Scope

Implement these tables first:

- `knowledge_bases`
- `documents`
- `document_chunks`
- `conversations`
- `messages`

Do not require users, workspaces, citations, or feedback to exist for the first milestone. If the current codebase has no user or workspace system yet, keep `knowledge_bases.workspace_id` and `conversations.user_id` nullable, omit hard foreign keys for them, or use the existing project convention for placeholder ownership. Prefer a migration path that can add `users`, `workspaces`, and `workspace_members` later without rewriting document or conversation records.

## Milestone Tables

### knowledge_bases

Required columns:

- `id`
- `workspace_id`
- `name`
- `description`
- `embedding_model`
- `created_at`

Use this as the top-level RAG collection. Store the embedding model used for chunks so retrieval can reject or migrate incompatible embeddings later.

### documents

Required columns:

- `id`
- `knowledge_base_id`
- `filename`
- `original_filename`
- `mime_type`
- `storage_key`
- `status`
- `page_count`
- `error_message`
- `created_at`
- `processed_at`

Use `knowledge_base_id` as a required foreign key to `knowledge_bases.id`. Use `status` to represent ingestion lifecycle states such as pending, processing, processed, or failed. Keep `error_message` nullable and set `processed_at` only after processing finishes successfully or according to the local convention if failures are timestamped.

### document_chunks

Required columns:

- `id`
- `document_id`
- `chunk_index`
- `content`
- `page_number`
- `section_title`
- `token_count`
- `metadata`
- `embedding vector(...)`

Use `document_id` as a required foreign key to `documents.id`. Keep `chunk_index` unique per document. Store source text in `content`, retrieval details in `metadata`, and vector data in `embedding` using the repository's chosen vector extension or database type. Keep the embedding dimension consistent with `knowledge_bases.embedding_model`.

### conversations

Required columns:

- `id`
- `user_id`
- `knowledge_base_id`
- `title`
- `created_at`
- `updated_at`

Use `knowledge_base_id` as a required foreign key to `knowledge_bases.id`. Keep `user_id` compatible with a later `users.id` relationship, but do not block the milestone if users are not implemented yet. Update `updated_at` when messages are added or conversation metadata changes.

### messages

Required columns:

- `id`
- `conversation_id`
- `role`
- `content`
- `model_name`
- `created_at`

Use `conversation_id` as a required foreign key to `conversations.id`. Keep `role` constrained to the app's chat roles such as user, assistant, or system. Store `model_name` for assistant/model-generated messages; allow it to be nullable for user messages if that matches local patterns.

## Future Tables

Plan for these later tables without implementing them in the first milestone unless requested:

- `users`: `id`, `email`, `password_hash`, `display_name`, `created_at`
- `workspaces`: `id`, `name`, `owner_id`, `created_at`
- `workspace_members`: `workspace_id`, `user_id`, `role`
- `message_citations`: `id`, `message_id`, `chunk_id`, `rank`, `similarity_score`, `quoted_text`
- `message_feedback`: `id`, `message_id`, `user_id`, `rating`, `comment`

When adding these later, wire ownership from users to workspaces, workspaces to knowledge bases, citations from assistant messages to chunks, and feedback from users to messages.

## Implementation Rules

- Follow existing migration, model, and repository conventions before adding new tools or directory patterns.
- Prefer explicit foreign keys among milestone tables: `documents.knowledge_base_id`, `document_chunks.document_id`, `conversations.knowledge_base_id`, and `messages.conversation_id`.
- Add indexes for common access paths: documents by knowledge base, chunks by document, conversations by knowledge base/user, messages by conversation, and vector similarity search on chunk embeddings when the database supports it.
- Keep timestamps timezone-aware if the stack supports it, and use database defaults for `created_at` where nearby migrations do so.
- Use JSON/JSONB or the local equivalent for `document_chunks.metadata`; avoid storing structured metadata as an opaque string.
- Add tests around migration creation, repository CRUD, status transitions, chunk ordering, and message ordering when those layers exist.
- Update backend docs or environment examples when the schema introduces required database extensions such as vector search.
