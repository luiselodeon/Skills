---
name: context-architect
description: Analyze a repository and build, upgrade or sync a modular Claude Code context architecture - hierarchical CLAUDE.md files with @imports, path-scoped .claude/rules/, .claude/standards/ built from a user interview, and a root scratchpad.md with living architecture notes. Delegates large repos to parallel subagents. Three modes - INIT (from scratch), UPGRADE (audit an existing setup and migrate it to best practices without losing content) and SYNC (update rules, standards, CLAUDE.md and scratchpad after repo changes). Use whenever the user wants to set up, audit, improve, reorganize, refresh or update CLAUDE.md files, the .claude folder, rules, standards or agent context for a codebase, or says "my CLAUDE.md is outdated", "apply best practices to my context", "sync scratchpad", "migrate GEMINI.md/AGENTS.md/.cursorrules to Claude", even without naming the skill.
---

# Claude Context Architect

Turns a repository into a modular, token-efficient Claude Code context system and keeps it accurate as the code evolves.

Four artifacts, each with a distinct job:

| Artifact | Job | Loaded |
|---|---|---|
| `CLAUDE.md` (root + scoped) | Identity, commands, directory map, `@imports` | Root at launch; subdirectory ones when Claude reads files there |
| `.claude/rules/*.md` | Conventions bound to file globs (`paths:` frontmatter) | When Claude touches a matching file |
| `.claude/standards/*.md` | Detailed shared specs (testing, API, security...) built from **user decisions** + scan | Only when `@imported` |
| `scratchpad.md` (repo root) | Living architecture map + change log + sync baseline | On demand (pointer, not import) |

Generated files are written in **English** by default (better instruction adherence, fewer tokens); talk to the user in their own language. If they ask for another language for the files, honor it.

## Pick the mode first

- **INIT** - no `CLAUDE.md`, `.claude/` or `scratchpad.md` exist and there is no other agent context to migrate -> "INIT workflow" below.
- **UPGRADE** - some context already exists (a `CLAUDE.md`, `.claude/`, `GEMINI.md`, `AGENTS.md`, `.cursorrules`...) but its structure or quality is below best practice: monolithic root file, no `@imports`, no `.claude/rules/` or `.claude/standards/`, wrong import syntax, duplicated text, no scratchpad, secrets, etc. Also the right mode when the user asks to "improve", "audit", "reorganize" or "apply best practices" -> read `references/upgrade-mode.md` and follow it.
- **SYNC** - the structure is sound and the user says things changed, asks to update/refresh it, or the drift check reports changes -> read `references/sync-mode.md` and follow it.

How to decide when it is not obvious: if any context file exists, run `scripts/audit_context.py <root>` first. Structural findings (high/medium) -> UPGRADE; a good score plus drift from `scripts/detect_drift.py` -> SYNC; nothing exists -> INIT. Say which mode you chose and why, in one line.

Environment note: with a local repo (Claude Code) write files directly, after the user approves the plan. In chat without repo access (claude.ai), ask for a zip of the repo or the tree plus manifests, run the scripts in the sandbox if a zip is provided, and deliver files as a zip or a single setup script.

## INIT workflow

### Step 1 - Scan (deterministic first)

Run `python <skill>/scripts/scan_repo.py <repo-root>`. It reports topology, languages, manifests, tooling, existing context files, a delegation verdict and suggested partitions. Do not hand-walk a big tree when the script can summarize it. If no filesystem access, ask for `tree -L 3 -I 'node_modules|.git'` plus the main manifest.

If any agent context already exists (`CLAUDE.md`, `.claude/`, `GEMINI.md`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`), this is not an INIT: switch to UPGRADE mode, which migrates it losslessly instead of overwriting.

### Step 2 - Delegate if the repo is large

If the scan says `DELEGATION: REQUIRED`, do not read the code yourself: read `references/subagent-delegation.md` and run one read-only subagent per partition in parallel, each returning a compact structured digest. Build everything after this point from the digests, so the main context stays small. If the repo is small, scan inline: read manifests, entry points and a sample of representative files per directory.

Either way, capture: topology, stack, entry points, module boundaries and dependencies, data flow, test setup, commands, conventions actually observed (cite a file for each), gotchas (generated code, legacy zones, do-not-touch areas).

### Step 3 - Interview the user about standards (mandatory, never skip)

The scan shows what the repo *does*; only the user can say what it *should* do. Always ask before writing `.claude/standards/`, even when config files hint at answers - then offer the detected value as the recommended default. Read `references/standards-questionnaire.md` for categories, option sets and how to batch questions.

Minimum coverage, asked in 1-2 rounds with the interactive question tool if available (`AskUserQuestion` in Claude Code), otherwise a numbered list in chat:

1. **Code style & documentation** - comments/docstrings policy (none / public API only / everything), naming, typing strictness, file/function size limits, error handling.
2. **Testing** - which test types, framework, coverage expectations, mocking boundaries, TDD or after, where tests live.
3. **API** - REST/GraphQL/RPC conventions, error envelope, versioning, validation, pagination, API docs.
4. **Security** - secrets, authn/authz, input validation, PII/logging, dependency policy, compliance.
5. **Workflow & autonomy** - commit/branch/PR conventions, and what Claude may do without asking (install deps, run migrations, push).

Skip a category only if it truly does not apply (e.g. no API in a CLI tool) and say so. End with one open question: "Anything else Claude must always or never do here?" If the user answers "use your judgment", proceed with scan-derived defaults and mark them as assumptions in the file.

### Step 4 - Design `.claude/standards/`

One concise file per topic, grounded in interview answers + scan findings. Start each file with a one-line provenance header so SYNC mode knows how to treat it:

```
> Source: decision (interview YYYY-MM-DD) | observed (scan)
```

- **decision** content is policy. It changes only when the user says so.
- **observed** content is fact about the repo. It is updated automatically when the repo changes.

Baseline files (when applicable): `code-style.md`, `testing.md`, `api-design.md`, `security.md`, `git-and-workflow.md`. Add a dedicated file for every significant cross-cutting pattern found (`state-management.md`, `database-and-orm.md`, `error-handling.md`, `observability.md`, `design-system.md`, `async-workers.md`...) so no finding is lost. Standards have no `paths` frontmatter. Keep each one actionable and short.

### Step 5 - Design `.claude/rules/`

Path-scoped conventions. Every rule file must start with valid YAML frontmatter:

```markdown
---
paths:
  - "**/*.test.ts"
  - "**/*.spec.ts"
---

# Testing Rules
- Mock network and DB calls in unit tests; co-locate fixtures in `__fixtures__/`.
- Deeper policy: see `.claude/standards/testing.md`.
```

Cover cross-cutting file types (tests, components, routes, models, config/env) and bounded areas (`terraform/**`, `.github/workflows/*`, `migrations/**`, `scripts/**`, legacy zones). Every glob must match real files, and quote globs that start with `*` or `{`. A rule that points to a standard uses a plain path mention rather than depending on `@import` support inside rules. Rules without `paths` load at every launch, so omit that only for truly global rules.

### Step 6 - Generate hierarchical `CLAUDE.md` files

Use the templates in `references/templates.md`.

- **Root `CLAUDE.md`:** project identity, architecture summary, stack, build/test/lint commands, directory map, a pointer to `scratchpad.md`, the **Context maintenance** block (so Claude keeps files current in normal sessions), and `@imports` only for short, repo-wide standards (they load every session).
- **Scoped `CLAUDE.md`** in every meaningful package/directory: that folder's responsibility plus `@imports` of the standards relevant to it. These load only when Claude works there, so heavier standards belong here.
- Never copy standards or rules inline; import or rely on glob matching.
- Import syntax in Claude Code is `@path/to/file.md` (not `@import`), resolved relative to the file containing it, up to 5 hops deep, and ignored inside code spans/fences.
- Keep each file under ~120 lines (hard ceiling 200).

### Step 7 - Create `scratchpad.md`

At the repo root, from `assets/scratchpad-template.md`. It is the living architecture memory: system overview, module map, data flow, key decisions, entry points, known hazards, open questions, and a rolling change log. Fill it from the scan/digests, keeping it factual and under ~200 lines. Reference it from the root `CLAUDE.md` by plain pointer ("read `scratchpad.md` before cross-module or architectural work"), not by `@import`, so it doesn't cost tokens every session. Ask the user whether to commit it (team-shared, default) or add it to `.gitignore` (personal).

### Step 8 - Confirm, write, verify

1. Show the plan: findings -> where each was routed, a tree of every file to create/modify, and which items are assumptions. Get approval before writing (skip the confirmation only if the user already said to just do it).
2. Write the files (or produce the zip/setup script when there is no repo access).
3. Run `python <skill>/scripts/detect_drift.py <repo-root>` to validate: broken imports, stale globs, dangling paths, oversized files. Fix what it reports.
4. Run `python <skill>/scripts/detect_drift.py <repo-root> --stamp` to record the sync baseline in `scratchpad.md`.
5. Offer (do not install unasked) the optional auto-sync helpers described in `references/sync-mode.md`: a `SessionStart` hook that surfaces drift and a `/sync-context` command. These edit `.claude/settings.json`, which is the user's configuration, so get explicit consent first.
6. Summarize in the user's language: what was created, key findings, assumptions to confirm, and how to trigger SYNC later.

## UPGRADE workflow (summary)

Full procedure, routing-table format and transformation recipes are in `references/upgrade-mode.md`. In short:

1. **Safety net** - clean git tree/branch, or copy the existing context files to a backup folder.
2. **Audit** - `audit_context.py` (score + findings) and `scan_repo.py` (repo facts; delegate to subagents when it says so).
3. **Inventory** - read every existing context file and build a routing table: each section goes to a standard (cross-cutting policy), a rule (file-type convention), a scoped `CLAUDE.md` (folder-specific), `scratchpad.md` (architecture facts), stays in the slim root, or is listed for approved deletion (duplicate, vague, obsolete).
4. **Gap interview** - confirm the policies extracted from the old files, then run the standards questionnaire only for uncovered topics (still mandatory for the core topics). See `references/standards-questionnaire.md` section 6.
5. **Plan and approval** - findings, routing table, before/after tree, assumptions.
6. **Apply** in dependency order: standards -> rules -> scoped `CLAUDE.md` -> slim root (with `@imports`, scratchpad pointer, maintenance block) -> scratchpad -> legacy-file integration.
7. **Verify** - lossless check against the routing table, `detect_drift.py`, `audit_context.py` again (no high findings, better score), then `detect_drift.py --stamp`.

Existing wording of team policies is preserved and tagged `Source: decision (migrated ...)`; nothing is dropped without the user's approval.

## Gotchas

- **Relative `@import` depth:** compute the path from the importing file (`../.claude/standards/x.md` from `src/`, `../../.claude/...` from `src/api/`). The drift script verifies this; run it.
- **Root imports are expensive:** everything imported from the root loads on every session. Import only what is truly global; push the rest into scoped `CLAUDE.md` files or path rules.
- **Exclude build/vendor dirs:** never put `CLAUDE.md` inside `node_modules/`, `.git/`, `dist/`, `build/`, `.next/`, `target/`, `__pycache__/`.
- **Don't invent conventions:** every claim in a generated file should trace to a file you saw, a digest, or a user answer. Mark guesses as assumptions.
- **Decisions vs. facts:** never rewrite a `Source: decision` standard because the code disagrees; flag the conflict to the user instead.
- **Secrets:** never copy values from `.env` files or credentials into context files; mention variable names only. If an audit finds one already in a context file, remove it, tell the user to rotate it, and do not echo the value.
- **Existing content is sacred in UPGRADE:** preserve wording and intent of user-authored policies; move and wire them, don't rewrite or silently drop them.
- **Valid frontmatter:** `paths` is a YAML list of glob strings in `rules/`; omit frontmatter in `standards/`, `CLAUDE.md` and `scratchpad.md` (which has only the sync comment).
