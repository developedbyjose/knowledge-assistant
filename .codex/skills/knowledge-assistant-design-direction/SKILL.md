---
name: knowledge-assistant-design-direction
description: "Project-local design direction for the Knowledge Assistant frontend. Use when adding, editing, or reviewing UI screens, layouts, components, Tailwind classes, CSS variables, empty states, forms, dashboards, status treatments, or frontend design-system choices for a calm internal enterprise tool."
---

# Knowledge Assistant Design Direction

## Overview

Use this skill to keep the Knowledge Assistant interface professional, calm, trustworthy, information-focused, and appropriate for an internal enterprise tool. Avoid making screens resemble flashy AI landing pages.

When this skill overlaps with `knowledge-assistant-structure`, use that skill for frontend file placement and this skill for visual direction, layout consistency, and component styling.

## Product Personality

The interface should feel:

- Professional
- Calm
- Trustworthy
- Information-focused
- Appropriate for an internal enterprise tool

Prefer practical workflows, clear hierarchy, and readable data over expressive marketing composition.

## Visual Principles

- Use no gradients.
- Use one restrained accent color.
- Prefer borders over heavy shadows.
- Use spacing to create hierarchy.
- Keep corner radii consistent.
- Use semantic colors only for statuses.
- Keep page widths and form patterns consistent.
- Use the same empty-state structure across modules.

Avoid decorative multi-color surfaces, oversized hero treatments, dramatic backgrounds, and visually loud AI branding patterns.

## Design System Colors

Use semantic CSS variables instead of direct hex values inside components.

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222 47% 11%;

  --card: 0 0% 100%;
  --card-foreground: 222 47% 11%;

  --muted: 210 40% 96%;
  --muted-foreground: 215 16% 47%;

  --border: 214 32% 91%;
  --input: 214 32% 91%;

  --primary: 221 83% 53%;
  --primary-foreground: 210 40% 98%;

  --secondary: 210 40% 96%;
  --secondary-foreground: 222 47% 11%;

  --destructive: 0 72% 51%;
  --destructive-foreground: 0 0% 100%;

  --ring: 221 83% 53%;
  --radius: 0.5rem;
}
```

Recommended use:

- Use a white or neutral page background.
- Use neutral cards.
- Use blue as the single primary accent.
- Use green only for success.
- Use amber only for warnings.
- Use red only for errors.
- Do not use decorative multi-color surfaces.

## Typography

Use one primary sans-serif typeface:

- Geist
- Inter
- System font stack

Suggested hierarchy:

| Element | Style |
| --- | --- |
| Page title | `text-2xl font-semibold tracking-tight` |
| Section title | `text-lg font-semibold` |
| Card title | `text-sm font-medium` |
| Body | `text-sm leading-6` |
| Secondary text | `text-sm text-muted-foreground` |
| Label | `text-sm font-medium` |
| Metadata | `text-xs text-muted-foreground` |

Avoid using bold text everywhere. Create hierarchy through size, spacing, and muted colors before adding weight.

## Spacing

Use a consistent spacing rhythm:

- 4px: icon and inline gaps
- 8px: compact component gaps
- 12px: form internals
- 16px: card spacing
- 24px: section spacing
- 32px: page-level spacing

Use spacing to separate related groups before adding extra containers, dividers, or shadows.

## Radius And Shadows

Use:

- `rounded-md` for inputs and buttons
- `rounded-lg` for cards and dialogs
- `shadow-sm` only when separation is necessary
- Borders for most surfaces

Avoid:

- Very rounded pill-shaped cards
- Large blurred shadows
- Different radius values on every component

## Component Guidance

- Keep page widths consistent for comparable workflows.
- Keep forms visually consistent across create/edit screens.
- Use neutral cards and bordered panels for dense information.
- Use badges and semantic color only for meaningful statuses.
- Keep empty states consistent across modules: icon or compact visual, concise title, short supporting text, and one clear action when applicable.
- Prefer compact, scannable layouts for knowledge bases, documents, conversations, and admin surfaces.
- Use direct product UI as the first screen for app routes; do not introduce marketing hero sections unless the user explicitly asks for a landing page.

## Reusable UI Patterns

Create shared application components instead of repeatedly styling raw shadcn components at call sites. Keep wrappers thin, predictable, and aligned with the product layout patterns.

For dropdown controls, use the shared `Select` primitive from `@/components/ui/select` with `SelectTrigger`, `SelectValue`, `SelectContent`, and `SelectItem`. Do not use a raw HTML `<select>` for application dropdowns. Preserve an associated label by matching its `htmlFor` to the `SelectTrigger` `id`, and provide an appropriate placeholder plus disabled states for loading or unavailable options.

Recommended shared components:

- `PageHeader`
- `PageContainer`
- `SectionHeader`
- `DataTable`
- `EmptyState`
- `StatusBadge`
- `ConfirmDialog`
- `FileDropzone`
- `UploadProgress`
- `KnowledgeBaseSelector`
- `ChatComposer`
- `AssistantMessage`
- `SourceCitation`
- `SourcePanel`
- `DocumentPreview`
- `ErrorState`
- `LoadingSkeleton`

Use `PageHeader` to keep page title, optional description, and actions consistent:

```tsx
type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: React.ReactNode;
};

export function PageHeader({
  title,
  description,
  actions,
}: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          {title}
        </h1>

        {description ? (
          <p className="text-sm text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>

      {actions}
    </div>
  );
}
```

## Accessibility Requirements

Treat accessibility as part of the project definition, not optional polish.

- Ensure keyboard-accessible navigation.
- Use visible focus states.
- Provide labels for every form field.
- Give icon buttons accessible names.
- Maintain sufficient color contrast.
- Communicate status with text, not color alone.
- Trap focus inside dialogs.
- Connect error messages to their fields.
- Support reduced-motion preferences.
- Use semantic headings.
- Use proper table markup for tabular data.

## Application Shell

Use this standard shell for authenticated application pages:

- Sticky top header with logo or workspace selector, global search, help, theme toggle, and profile controls.
- Fixed or collapsible left sidebar at approximately 240-260px on desktop.
- Sidebar navigation: New chat, Chat, Documents, Knowledge, Activity, Settings.
- Main content starts with breadcrumb when useful, then page title and page actions.
- Use maximum readable width for settings, forms, and authentication-adjacent flows.
- Use full-width content for tables, chat, and dense operational views.

On mobile:

- Convert the sidebar to a sheet.
- Keep primary page actions visible.
- Convert document tables to stacked records where needed.
- Convert citation/source panels to a bottom sheet.
- Keep the chat input sticky near the bottom.

## Screen Patterns

### Authentication

- Use a centered card with the product mark and short description.
- Include sign in and register pages; forgot password can be added later.
- Avoid illustrations, gradients, and marketing-style composition.
- Show clear validation messages next to the relevant fields or form area.

### Dashboard

Show practical operational summaries only:

- Total documents
- Ready documents
- Documents being processed
- Recent conversations
- Recent uploads
- Quick actions

Do not add charts merely to fill space. Use metrics only when they are meaningful.

### Knowledge Bases

Each knowledge base card should show:

- Name
- Description
- Document count
- Last updated
- Status
- Primary Open action
- Secondary actions in a dropdown menu

### Documents

Use a desktop table with these columns:

- Name
- Type
- Knowledge base
- Size
- Status
- Uploaded
- Actions

Include search, status filter, upload action, empty state, upload progress, and processing error details.

Use these status badge patterns:

| Status | Treatment |
| --- | --- |
| Queued | Secondary |
| Processing | Outline with spinner |
| Ready | Success |
| Failed | Destructive |

### Upload Dialog

Model upload as a clear sequence:

1. Select files
2. Choose knowledge base
3. Validate files
4. Show upload progress
5. Show processing status

Use a dashed drop zone and also include a normal file-selection button for accessibility.

### Chat

Use a two-panel desktop layout:

- Main conversation panel for user messages, document-style assistant answers, follow-up questions, and sticky input.
- Sources panel for cited documents, page numbers, and relevant excerpts.

Treat the sources panel as a core product feature because it differentiates the app from a basic chatbot. Avoid chat bubbles for long assistant answers; use clean document-style answer blocks for readability.

Assistant responses should support:

- Copy
- Helpful
- Not helpful
- View sources

### Settings

Use vertical navigation or tabs:

- General
- Model
- Retrieval
- Members
- Security

Retrieval settings can include:

- Number of results
- Similarity threshold
- Chunk size
- Chunk overlap
- Reranking toggle

For portfolio demo work, consider placing retrieval controls in an Advanced section so reviewers can see that the app supports configurable retrieval systems.
