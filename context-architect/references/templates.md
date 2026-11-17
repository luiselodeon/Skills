# Output templates

Skeletons for generated files. Fill with repo-specific content; delete sections that do not apply. Contents: root CLAUDE.md, scoped CLAUDE.md, rule, standard, setup script advice.

## Root `CLAUDE.md`

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
- `apps/web/` - <responsibility> (see its CLAUDE.md)
- `apps/api/` - <responsibility>
- `infra/` - <responsibility>

## Standards (repo-wide)
@.claude/standards/code-style.md
@.claude/standards/git-and-workflow.md

## Working notes
Read `scratchpad.md` before cross-module or architectural work.

## Context maintenance
<paste the block from sync-mode.md section 8>
```

Import only short, global standards here; each import loads every session.

## Scoped `CLAUDE.md` (e.g. `apps/api/CLAUDE.md`)

```markdown
# API service

<Responsibility in 1-2 lines; what this folder must NOT do.>

## Local commands
- `<cmd>`

## Conventions specific to this folder
- <bullet, each traceable to code or a decision>

## Standards
@../../.claude/standards/api-design.md
@../../.claude/standards/security.md
```

The `../` count equals the folder depth below the repo root (`apps/api/` -> two levels). Verify with `detect_drift.py`.

## Rule (`.claude/rules/<name>.md`)

```markdown
---
paths:
  - "apps/api/src/routes/**/*.ts"
  - "apps/api/src/controllers/**/*.ts"
---

# API route rules
- Validate every request body with the shared schema layer before use.
- Return errors in the standard envelope (details: `.claude/standards/api-design.md`).
```

Frontmatter is required; globs must match real files; quote globs that start with `*` or `{`.

## Standard (`.claude/standards/<topic>.md`)

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

No `paths` frontmatter in standards.

## Delivery without repo access

Show findings and a tree of files, then the full contents under exact path headings (`### .claude/standards/security.md`), and provide one setup script (bash heredocs, plus PowerShell if the user is on Windows) or a zip that creates every directory and file in one run. Use quoted heredoc delimiters (`<<'EOF'`) so `$`, backticks and `@` are not expanded.
