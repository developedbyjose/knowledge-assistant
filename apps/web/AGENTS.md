# Web Agent

Follow these instructions for all work under `apps/web`.

## UI Planning Agent

Act as a UI planning agent before executing any user-visible frontend change.
Planning is a required first phase of the work, not an optional cleanup step.

Before editing code:

1. Inspect the affected route and the nearest comparable screens, shared
   components, layout primitives, design tokens, loading/empty/error states,
   and responsive patterns. Do not plan from the requested screen in isolation.
2. Write a concise implementation plan that identifies:
   - the user goal and primary workflow;
   - the existing patterns and components that will be reused;
   - the intended page hierarchy, responsive behavior, and UI states;
   - accessibility requirements and validation/error behavior;
   - any new shared pattern or deliberate exception to the current system;
   - the focused checks that will verify the result.
3. Compare the plan against the consistency checklist below. Resolve conflicts
   in favor of existing product patterns unless the user explicitly requests a
   design-system change.
4. Execute only after the plan is coherent. If implementation reveals a
   material mismatch, update the plan before continuing.

For tiny, non-visual fixes, the plan may be one or two sentences. For a new
screen, major workflow, or design-system change, make it detailed enough to
review before implementation. Keep plans in the task conversation by default;
create a file under `docs/` only when the plan is durable project knowledge.

### UI Consistency Checklist

- Reuse the application shell, page container, page header, navigation, form,
  table, dialog, status, loading, error, and empty-state patterns already used
  by comparable screens.
- Use semantic CSS variables and the established spacing, typography, radius,
  and restrained blue accent. Do not introduce gradients, decorative color,
  heavy shadows, or one-off styling without a documented reason.
- Keep labels, action placement, terminology, icon usage, and feedback behavior
  consistent across related workflows.
- Define desktop and mobile behavior before implementation, including overflow,
  sticky actions, side panels, sheets, and table-to-card transformations.
- Include loading, empty, success, validation, permission, and failure states
  relevant to the workflow; do not design only the happy path.
- Preserve keyboard access, visible focus, semantic headings, form labels,
  accessible names, sufficient contrast, and text-based status communication.
- Prefer extending an existing shared component over creating a visually
  competing pattern. Promote a new shared component only when reuse is real.
- Review the finished UI against the plan and the nearest comparable screens,
  then run the narrowest relevant lint, test, build, and responsive checks.

## Folder Structure

- `src/app/`: Next.js App Router routes, layouts, loading states, error
  boundaries, and route-level composition.
- `src/components/ui/`: primitive reusable UI components.
- `src/components/layout/`: application shell, page containers, page headers,
  navigation, and layout primitives.
- `src/components/chat/`, `src/components/documents/`, and other domain folders:
  reusable domain components shared by routes or feature modules.
- `src/features/`: feature-level orchestration when a workflow grows beyond a
  single route file.
- `src/hooks/`: reusable React hooks.
- `src/lib/`: browser-safe API wrappers, utilities, constants, formatters, and
  client configuration.
- `tests/`: frontend unit, component, accessibility, and integration tests when
  added.

## Architecture Rules

- Keep route files focused on page composition. Move reusable behavior into
  components, hooks, feature modules, or `src/lib`.
- Call the backend through `src/lib/api.ts` or a generated client. Do not
  duplicate endpoint strings across components when a shared client function
  exists.
- Keep browser code independent from backend Python internals. Shared contracts
  belong in `packages/api-client` or `packages/shared-types` when they need to be
  consumed across packages.
- Use existing shadcn-style UI primitives and `lucide-react` icons before adding
  new component libraries.
- Preserve the product direction: calm internal enterprise UI, neutral surfaces,
  restrained blue accent, borders over heavy shadows, and no marketing hero
  treatment for application screens.

## Security Rules

- Treat all API responses, user-entered text, uploaded file names, document
  excerpts, citations, and model output as untrusted content.
- Do not render untrusted HTML. Prefer plain text rendering. If rich text is
  required, sanitize it with an approved sanitizer before rendering.
- Do not expose secrets through `NEXT_PUBLIC_*`. Only publish values that are
  safe for every browser user to inspect.
- Keep authentication tokens in secure, HTTP-only cookies when auth is
  implemented. Avoid localStorage or sessionStorage for long-lived tokens.
- Include CSRF protection or same-site cookie strategy when browser-authenticated
  state-changing requests are added.
- Validate files client-side for user feedback, but rely on backend validation
  for enforcement.
- Do not log private document text, auth tokens, raw prompts, or full API
  responses containing sensitive content to the browser console.
- Escape user-provided values in URLs and query strings with standard APIs such
  as `URL` and `URLSearchParams`.
- Keep dependency additions minimal and avoid packages with unmaintained or
  unsafe transitive dependencies.

## Accessibility And UX Expectations

- Ensure keyboard navigation, visible focus states, semantic headings, form
  labels, accessible names for icon buttons, and text-based status indicators.
- Use existing page containers, headers, status badges, dialogs, sheets, tables,
  and chat components before creating new patterns.
- Keep dense operational screens scannable. Use tables for tabular document data
  on desktop and stacked records on mobile.
- Keep chat sources visible as a core workflow, with a desktop side panel and a
  mobile-friendly sheet pattern when needed.

## Testing Expectations

- Run `pnpm lint` for frontend code changes when possible.
- Add component or integration tests for stateful workflows, auth-sensitive UI,
  upload behavior, streaming chat behavior, and user-visible error states.
- Verify responsive layouts for new screens or major UI changes.
