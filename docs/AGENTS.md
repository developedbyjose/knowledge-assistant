# Documentation Agent

Follow these instructions for all work under `docs/`.

## Purpose

Create durable project documentation that helps two audiences:

- returning contributors quickly refresh their understanding of the product,
  architecture, current behavior, and important decisions;
- new users and developers understand what the project does, how its major
  parts fit together, and where to go for setup or implementation details.

Prefer a small set of trustworthy, well-linked documents over many overlapping
notes. Documentation must describe the repository as it exists, not the system
the author hopes to build later.

## Start With Evidence

Before creating or substantially updating a document:

1. Read the root `AGENTS.md` and any more-specific `AGENTS.md` files for the
   areas being documented.
2. Inspect the relevant source code, configuration, migrations, tests, example
   environment files, and operating commands. Do not rely on filenames or old
   documentation alone.
3. Check the current documents in `docs/` and update an existing source of truth
   when possible instead of creating a duplicate.
4. Use tests and runtime configuration to confirm important behavior, defaults,
   limits, and failure cases.
5. When a fact cannot be verified, label it clearly as planned, assumed,
   unknown, or a known limitation. Never present speculation as current
   behavior.

## Documentation Map

Keep durable information in the document that owns it:

- `architecture.md`: system boundaries, component responsibilities, runtime
  topology, persistence, and end-to-end data flows.
- `api.md`: versioned endpoints, authentication and authorization behavior,
  request/response contracts, streaming events, errors, and compatibility
  notes.
- `retrieval-evaluation.md`: ingestion, chunking, embeddings, retrieval,
  generation, citations, fixtures, quality metrics, baselines, and known RAG
  limitations.
- `decisions/`: architecture decision records for durable choices and their
  tradeoffs. Create this directory only when the first decision record is
  needed.
- `screenshots/`: images that directly support maintained documentation. Avoid
  decorative or quickly outdated captures.

If a new document is necessary, give it one clear owner topic and link it from
the closest overview document. Do not create generic files such as `notes.md`,
`misc.md`, or date-stamped status dumps as durable project documentation.

## Required Content For Refresh And Onboarding Docs

When the scope calls for a project overview, onboarding guide, or major refresh,
make it easy to answer these questions in order:

1. What problem does Knowledge Assistant solve, and who is it for?
2. What can the product do today, and what is explicitly not implemented?
3. How are `apps/web`, `apps/api`, shared packages, infrastructure, and storage
   separated?
4. How does a document move from upload through parsing, chunking, embedding,
   storage, retrieval, answer generation, citation, and feedback?
5. What are the important domain entities and relationships?
6. What external services and environment variables are required?
7. How does a developer run, test, and troubleshoot the relevant part locally?
8. Where should a developer make common frontend, backend, API, database, and
   RAG changes?
9. What security boundaries, operational constraints, and known limitations
   must not be missed?
10. Which files are the best next reading for deeper detail?

Use a short "Quick refresh" or "At a glance" section near the top of long
overview documents. Put setup commands in copyable code blocks and state the
directory from which each command runs.

## Writing Standards

- Lead with purpose and current behavior, then explain implementation detail.
- Use plain language and define project-specific terms on first use.
- Prefer short sections, descriptive headings, and lists that can be scanned.
- Use diagrams only when they clarify a multi-step flow or system boundary.
  Keep diagrams small, label trust boundaries, and explain them in prose.
- Link to repository-relative files and related docs instead of copying large
  code samples that will drift.
- Include concrete names for routes, services, providers, tables, settings, and
  commands when those details help a reader navigate the code.
- Separate current behavior, planned work, and known limitations explicitly.
- Add a "Last verified" date only when the document has a clear verification
  process; never use a date as a substitute for checking the source.
- Do not include secrets, credentials, private document content, raw prompts,
  authorization headers, or real provider keys. Use safe placeholders.

## Accuracy And Maintenance

Update documentation in the same change when any of these move:

- application or module boundaries;
- API routes, schemas, authentication, errors, or SSE event behavior;
- database tables, relationships, migrations, or retention behavior;
- document ingestion, retrieval, ranking, generation, citation, or evaluation;
- provider selection, environment variables, ports, Docker services, or common
  operating commands;
- important user workflows or visible product limitations.

Keep terminology consistent with source code. Remove stale claims rather than
adding contradictory caveats. If two documents disagree, inspect the code and
tests, correct the owning document, and update links or summaries elsewhere.

## Verification Checklist

Before finishing a documentation change:

- confirm every referenced path exists;
- confirm commands and configuration names against the current repository;
- confirm endpoint and schema details against routes, schemas, and tests;
- confirm database claims against models and migrations;
- confirm RAG claims against services, providers, fixtures, and evaluation
  tests;
- search for conflicting or duplicated statements in `docs/`;
- review links, headings, code fences, and diagrams for readable Markdown;
- run the narrowest relevant checks when the document makes testable claims.

In the final handoff, state which sources were verified and call out anything
that could not be validated.
