# Output templates

Skeletons for generated files. Fill with repo-specific content; delete sections that do not apply. Contents: root GEMINI.md, scoped GEMINI.md, rule, standard, delivery without repo access.

## Root `GEMINI.md`

```markdown
# <Project name>

<One-paragraph identity: what it is, who uses it, main tech.>

## Architecture
<3-6 lines: topology, main components, how they talk. Details live in `scratchpad.md`.>

## Commands
- Install: `<cmd>`
- Dev: `<cmd>`
- Build: `<cmd>`
- Test: `<cmd>` (single file: `<cmd>`)
- Lint/format: `<cmd>`

## Directory map
- `apps/web/` - <responsibility> (see its GEMINI.md)
- `apps/api/` - <responsibility>
- `infra/` - <responsibility>

## Standards (repo-wide)
@./standards/code-style.md
@./standards/git-and-workflow.md

## Rules index
Before creating or editing a file that matches a glob below, read its rule file first.

| Glob | Rule |
|---|---|
| `**/*.test.ts`, `**/*.spec.ts` | `.gemini/rules/tests.md` |
| `.github/workflows/*` | `.gemini/rules/ci-cd.md` |

## Working notes
Read `scratchpad.md` before cross-module or architectural work.

## Context maintenance
<paste the block from sync-mode.md section 8>
```

Import only short, global standards here; each import is sent with every prompt. List only **cross-cutting** rules in the index; folder-bound rules are imported from that folder's scoped file. The import lines must sit on their own line, outside code fences, and end in `.md`.

## Scoped `GEMINI.md` (e.g. `apps/api/GEMINI.md`)

```markdown
# API service

<Responsibility in 1-2 lines; what this folder must NOT do.>

## Local commands
- `<cmd>`

## Conventions specific to this folder
- <bullet, each traceable to code or a decision>

## Standards and rules
@../../standards/api-design.md
@../../standards/security.md
@../../.gemini/rules/api-routes.md
```

The `../` count equals the folder depth below the repo root (`apps/api/` -> two levels). A path that starts with `../` is already explicit; for same-folder files write `@./file.md`. Verify with `detect_drift.py`.

## Rule (`.gemini/rules/<name>.md`)

```markdown
---
paths:
  - "apps/api/src/routes/**/*.ts"
  - "apps/api/src/controllers/**/*.ts"
---

# API route rules
- Validate every request body with the shared schema layer before use.
- Return errors in the standard envelope (details: `standards/api-design.md`).
```

Frontmatter is required (it is the metadata the scripts use); globs must match real files; quote globs that start with `*` or `{`. A rule does nothing until it is wired: imported from the scoped `GEMINI.md` of its folder (as above) or listed in the root Rules index.

## Standard (`standards/<topic>.md`)

```markdown
> Source: decision (interview 2026-11-17) | observed (scan)

# Testing standard

## Policy
- <imperative rule> (decision)
- <imperative rule> (assumption - confirm)

## Observed in repo
- Framework: Vitest; tests co-located as `*.test.ts` (e.g. `apps/web/src/lib/format.test.ts`)

## Verification
Run `<cmd>` before declaring work done.
```

No frontmatter in standards.

## Delivery without repo access

Show findings and a tree of files, then the full contents under exact path headings (`### standards/security.md`), and provide one setup script (bash heredocs, plus PowerShell if the user is on Windows) or a zip that creates every directory and file in one run. Use quoted heredoc delimiters (`<<'EOF'`) so `$`, backticks and `@` are not expanded.
