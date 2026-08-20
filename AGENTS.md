# Knowledge Assistant Agents

These instructions apply to the whole repository. More specific guidance in
`apps/api/AGENTS.md` and `apps/web/AGENTS.md` takes precedence inside those
folders.

## Product Boundaries

- Treat this as a monorepo with separate applications:
  - `apps/api` owns the FastAPI backend, persistence, RAG pipeline, workers,
    migrations, and backend tests.
  - `apps/web` owns the Next.js frontend, routes, UI components, browser
    helpers, hooks, and frontend tests.
  - `packages/api-client` owns generated or handwritten TypeScript API clients.
  - `packages/shared-types` owns TypeScript contracts consumed by more than one
    package.
  - `docs` owns durable architecture, API, retrieval, and decision records.
  - `infrastructure` owns deployment scripts and operational support files.

## Structure Rules

- Keep code in the app that owns the behavior. Do not couple frontend code to
  backend internals or move Python-only contracts into TypeScript packages.
- Use existing folder patterns before adding new top-level directories.
- Keep route files thin and compose behavior from local services, components, or
  feature modules.
- Update docs when changing architecture, endpoint contracts, auth behavior,
  runtime topology, retrieval behavior, environment variables, or operating
  commands.
- Add tests close to the changed behavior. Prefer focused tests over broad
  rewrites.

## Security Rules

- Never commit secrets, tokens, credentials, private keys, `.env` contents, or
  provider API keys. Put required variables in `.env.example` with safe example
  values.
- Validate and sanitize all untrusted input at the boundary where it enters the
  system.
- Fail closed for authentication and authorization. Do not introduce default
  allow behavior for protected resources.
- Do not log secrets, raw authorization headers, private document content, or
  full prompts unless explicitly required for a safe local test fixture.
- Keep dependency changes minimal and prefer well-maintained packages. Avoid
  adding a package for small utility behavior already available in the standard
  library or existing dependencies.
- Preserve least privilege in Docker, CORS, database access, file uploads, and
  external provider configuration.
- Treat uploaded files and retrieved document text as untrusted content. Do not
  execute uploaded content or use it to build shell commands.
- Use parameterized queries or ORM query APIs. Do not interpolate user input into
  SQL or shell commands.

## Quality Gate

- Before finishing a code change, run the narrowest relevant checks available:
  backend tests for API changes, frontend lint/build checks for web changes, and
  contract/docs checks for cross-app changes.
- If a check cannot be run, state why and name the residual risk.
