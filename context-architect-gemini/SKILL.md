---
name: context-architect-gemini
description: Analyze a repository and build, upgrade or sync a modular Gemini CLI context architecture - hierarchical GEMINI.md files with @./imports, file-type rules in .gemini/rules/ (wired through a Rules index or scoped GEMINI.md imports), standards/ at the repo root built from a user interview, and a root scratchpad.md with living architecture notes. Delegates large repos to subagents or sequential digests. Three modes - INIT (from scratch), UPGRADE (audit an existing setup and migrate it to best practices without losing content) and SYNC (update rules, standards, GEMINI.md and scratchpad after repo changes). Use whenever the user wants to set up, audit, improve, reorganize, refresh or update GEMINI.md files, the .gemini folder, rules, standards or agent context for a codebase, or says "my GEMINI.md is outdated", "the /init file is too generic", "apply best practices to my context", "sync scratchpad", "migrate CLAUDE.md/AGENTS.md/.cursorrules to Gemini", even without naming the skill.
---

# Gemini Context Architect

Turns a repository into a modular, token-efficient Gemini CLI context system and keeps it accurate as the code evolves.

Four artifacts, each with a distinct job:

| Artifact | Job | Loaded |
|---|---|---|
| `GEMINI.md` (root + scoped) | Identity, commands, directory map, Rules index, `@./imports` | Global + root/ancestor files at launch; subdirectory files either by startup scan or just-in-time when a tool touches that folder (depends on CLI version) |
| `.gemini/rules/*.md` | Conventions for file types/areas (`paths:` frontmatter = metadata) | **Only when wired**: a Rules index line in root `GEMINI.md`, or an `@./` import from a scoped `GEMINI.md` |
| `standards/*.md` | Detailed shared specs (testing, API, security...) built from **user decisions** + scan | Only when `@./imported` |
| `scratchpad.md` (repo root) | Living architecture map + change log + sync baseline | On demand (pointer, not import) |

Two facts shape every design choice. First, Gemini CLI concatenates every loaded `GEMINI.md` (imports already inlined) and sends it with **every prompt**, so anything imported high in the tree is paid for on every turn. Second, Gemini CLI has **no glob-triggered rule loading**: a rule file nobody points to is dead text. Step 5 explains how rules get wired.

Generated files are written in **English** by default (better instruction adherence, fewer tokens); talk to the user in their own language. If they ask for another language for the files, honor it.

## Pick the mode first

- **INIT** - no `GEMINI.md`, `.gemini/` or `scratchpad.md` exist and there is no other agent context to migrate -> "INIT workflow" below.
- **UPGRADE** - some context already exists (a `GEMINI.md` from `/init` or hand-written, `.gemini/`, `CLAUDE.md`/`.claude/`, `AGENTS.md`, `.cursorrules`...) but its structure or quality is below best practice: monolithic root file, no `@./imports`, no rules/standards, imports of non-`.md` files, rules that nothing loads, duplicated text, no scratchpad, secrets, etc. Also the right mode when the user asks to "improve", "audit", "reorganize" or "apply best practices" -> read `references/upgrade-mode.md` and follow it.
- **SYNC** - the structure is sound and the user says things changed, asks to update/refresh it, or the drift check reports changes -> read `references/sync-mode.md` and follow it.

How to decide when it is not obvious: if any context file exists, run `scripts/audit_context.py <root>` first. Structural findings (high/medium) -> UPGRADE; a good score plus drift from `scripts/detect_drift.py` -> SYNC; nothing exists -> INIT. Say which mode you chose and why, in one line.

Environment note: with a local repo (Gemini CLI) write files directly, after the user approves the plan. In a chat without repo access (Gemini app, AI Studio), ask for a zip of the repo or the tree plus manifests, run the scripts if code execution is available, and deliver files as a zip or a single setup script. After writing, tell the user to run `/memory show` to inspect what is loaded and `/memory reload` (older CLI versions: `/memory refresh`) to pick up edits.

## INIT workflow

### Step 1 - Scan (deterministic first)

Run `python <skill>/scripts/scan_repo.py <repo-root>`. It reports topology, languages, manifests, tooling, existing context files, a delegation verdict and suggested partitions. Do not hand-walk a big tree when the script can summarize it. If no filesystem access, ask for `tree -L 3 -I 'node_modules|.git'` plus the main manifest.

If any agent context already exists (`GEMINI.md`, `.gemini/`, `CLAUDE.md`, `.claude/`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`), this is not an INIT: switch to UPGRADE mode, which migrates it losslessly instead of overwriting.

### Step 2 - Delegate if the repo is large

If the scan says `DELEGATION: REQUIRED`, do not read the code yourself: read `references/subagent-delegation.md` and analyze one partition at a time (or in parallel when the CLI exposes subagents), each returning a compact structured digest. Build everything after this point from the digests, so the main context stays small. If the repo is small, scan inline: read manifests, entry points and a sample of representative files per directory.

Either way, capture: topology, stack, entry points, module boundaries and dependencies, data flow, test setup, commands, conventions actually observed (cite a file for each), gotchas (generated code, legacy zones, do-not-touch areas).

### Step 3 - Interview the user about standards (mandatory, never skip)

The scan shows what the repo *does*; only the user can say what it *should* do. Always ask before writing `standards/`, even when config files hint at answers - then offer the detected value as the recommended default. Read `references/standards-questionnaire.md` for categories, option sets and how to batch questions.

Minimum coverage, asked in 1-2 rounds with the CLI's interactive question tool if it has one, otherwise a numbered list in chat:

1. **Code style & documentation** - comments/docstrings policy (none / public API only / everything), naming, typing strictness, file/function size limits, error handling.
2. **Testing** - which test types, framework, coverage expectations, mocking boundaries, TDD or after, where tests live.
3. **API** - REST/GraphQL/RPC conventions, error envelope, versioning, validation, pagination, API docs.
4. **Security** - secrets, authn/authz, input validation, PII/logging, dependency policy, compliance.
5. **Workflow & autonomy** - commit/branch/PR conventions, and what Gemini may do without asking (install deps, run migrations, push).

Skip a category only if it truly does not apply (e.g. no API in a CLI tool) and say so. End with one open question: "Anything else Gemini must always or never do here?" If the user answers "use your judgment", proceed with scan-derived defaults and mark them as assumptions in the file.

### Step 4 - Design `standards/`

One concise file per topic, grounded in interview answers + scan findings. Start each file with a one-line provenance header so SYNC mode knows how to treat it:

```
> Source: decision (interview YYYY-MM-DD) | observed (scan)
```

- **decision** content is policy. It changes only when the user says so.
- **observed** content is fact about the repo. It is updated automatically when the repo changes.

Baseline files (when applicable): `code-style.md`, `testing.md`, `api-design.md`, `security.md`, `git-and-workflow.md`. Add a dedicated file for every significant cross-cutting pattern found (`state-management.md`, `database-and-orm.md`, `error-handling.md`, `observability.md`, `design-system.md`, `async-workers.md`...) so no finding is lost. Standards have no frontmatter. Keep each one actionable and short. Imports only work on `.md` files, so standards are always `.md`.

### Step 5 - Design `.gemini/rules/` and wire every rule

Rules hold conventions for file types and bounded areas. Every rule file starts with YAML frontmatter; here `paths:` is **metadata** (it lets the scripts verify the globs and lets you wire the rule), not an automatic trigger:

```markdown
---
paths:
  - "**/*.test.ts"
  - "**/*.spec.ts"
---

# Testing Rules
- Mock network and DB calls in unit tests; co-locate fixtures in `__fixtures__/`.
- Deeper policy: see `standards/testing.md`.
```

Cover cross-cutting file types (tests, components, routes, models, config/env) and bounded areas (`terraform/**`, `.github/workflows/*`, `migrations/**`, `scripts/**`, legacy zones). Every glob must match real files; quote globs that start with `*` or `{`.

**Wiring (mandatory - `detect_drift.py` reports `unwired-rule` otherwise):**

- **Folder-bound rule** (all its globs live under one folder, e.g. `apps/api/src/routes/**`): `@./`-import it from that folder's scoped `GEMINI.md`. It then loads only when Gemini works there.
- **Cross-cutting rule** (globs span folders, e.g. `**/*.test.ts`): add one row to the `## Rules index` table in the root `GEMINI.md` (glob -> rule file) with the instruction "before creating or editing a file matching a glob, read its rule". The rule body is not loaded until needed. This relies on the model following the instruction, so keep rule files short and tell the user it is a convention, not an enforced trigger.
- Never import every rule from the root; that defeats the savings.
- A rule that points to a standard uses a plain path mention, not a chained import.

### Step 6 - Generate hierarchical `GEMINI.md` files

Use the templates in `references/templates.md`.

- **Root `GEMINI.md`:** project identity, architecture summary, stack, build/test/lint commands, directory map, the **Rules index**, a pointer to `scratchpad.md`, the **Context maintenance** block (so Gemini keeps files current in normal sessions), and `@./imports` only for short, repo-wide standards (they load on every prompt).
- **Scoped `GEMINI.md`** in every meaningful package/directory: that folder's responsibility plus `@./` imports of the standards and rules relevant to it. Heavier standards belong here.
- Never copy standards or rules inline; import them or reference them from the Rules index.
- Import syntax in Gemini CLI is `@./path/to/file.md` (also `@../x.md`; absolute paths work but are not portable). Only `.md` files are imported, paths resolve relative to the file containing the import, circular imports are blocked, and imports inside code spans/fences are ignored. Always write the explicit `./` or `../`. Keep chains at most 3 levels deep.
- Keep each file under ~120 lines (hard ceiling 200).

### Step 7 - Create `scratchpad.md`

At the repo root, from `assets/scratchpad-template.md`. It is the living architecture memory: system overview, module map, data flow, key decisions, entry points, known hazards, open questions, and a rolling change log. Fill it from the scan/digests, keeping it factual and under ~200 lines. Reference it from the root `GEMINI.md` by plain pointer ("read `scratchpad.md` before cross-module or architectural work"), not by `@import`, so it doesn't cost tokens on every prompt. Ask the user whether to commit it (team-shared, default) or add it to `.gitignore` (personal).

### Step 8 - Confirm, write, verify

1. Show the plan: findings -> where each was routed, a tree of every file to create/modify, and which items are assumptions. Get approval before writing (skip the confirmation only if the user already said to just do it).
2. Write the files (or produce the zip/setup script when there is no repo access).
3. Run `python <skill>/scripts/detect_drift.py <repo-root>` to validate: broken or non-`.md` imports, unwired rules, stale globs, dangling paths, oversized files. Fix what it reports.
4. Run `python <skill>/scripts/detect_drift.py <repo-root> --stamp` to record the sync baseline in `scratchpad.md`.
5. Offer (do not install unasked) the optional auto-sync helpers described in `references/sync-mode.md`: a `SessionStart` hook that surfaces drift and a `/sync-context` custom command. The hook edits `.gemini/settings.json`, which is the user's configuration, so get explicit consent first.
6. Tell the user to run `/memory show` to confirm what actually loads, then summarize in their language: what was created, key findings, assumptions to confirm, and how to trigger SYNC later.

## UPGRADE workflow (summary)

Full procedure, routing-table format and transformation recipes are in `references/upgrade-mode.md`. In short:

1. **Safety net** - clean git tree/branch, or copy the existing context files to a backup folder.
2. **Audit** - `audit_context.py` (score + findings) and `scan_repo.py` (repo facts; delegate when it says so).
3. **Inventory** - read every existing context file and build a routing table: each section goes to a standard (cross-cutting policy), a rule (file-type convention), a scoped `GEMINI.md` (folder-specific), `scratchpad.md` (architecture facts), stays in the slim root, or is listed for approved deletion (duplicate, vague, obsolete).
4. **Gap interview** - confirm the policies extracted from the old files, then run the standards questionnaire only for uncovered topics (still mandatory for the core topics). See `references/standards-questionnaire.md` section 6.
5. **Plan and approval** - findings, routing table, before/after tree, assumptions.
6. **Apply** in dependency order: standards -> rules -> scoped `GEMINI.md` (with rule imports) -> slim root (with `@./imports`, Rules index, scratchpad pointer, maintenance block) -> scratchpad -> legacy-file integration.
7. **Verify** - lossless check against the routing table, `detect_drift.py`, `audit_context.py` again (no high findings, better score), then `detect_drift.py --stamp`.

Existing wording of team policies is preserved and tagged `Source: decision (migrated ...)`; nothing is dropped without the user's approval.

## Gotchas

- **Relative import paths:** compute them from the importing file (`../standards/x.md` from `src/`, `../../standards/x.md` or `../../.gemini/rules/r.md` from `src/api/`) and keep the leading `./` or `../`. The drift script verifies this; run it.
- **Everything loaded is sent every prompt:** the root and its transitive imports are the most expensive tokens in the repo. Import only what is truly global; push the rest into scoped `GEMINI.md` files or the Rules index.
- **Scoped-file loading differs by CLI version:** some versions scan subdirectories at startup, newer ones load a folder's `GEMINI.md` when a tool first touches it. Design for both (keep scoped files small, never assume a scoped file is "off") and let `/memory show` settle what the user's version does.
- **Imports are `.md` only:** anything else (`.txt`, `.json`, `.yaml`) fails. Point to such files in prose instead of importing them.
- **Rules are not auto-triggered:** a rule must be imported by a scoped `GEMINI.md` or listed in the Rules index, otherwise it is orphaned.
- **Exclude build/vendor dirs:** never put `GEMINI.md` inside `node_modules/`, `.git/`, `dist/`, `build/`, `.next/`, `target/`, `__pycache__/`.
- **Don't invent conventions:** every claim in a generated file should trace to a file you saw, a digest, or a user answer. Mark guesses as assumptions.
- **Decisions vs. facts:** never rewrite a `Source: decision` standard because the code disagrees; flag the conflict to the user instead.
- **Secrets:** never copy values from `.env` files or credentials into context files; mention variable names only. `.gemini/.env` can hold the user's API key: make sure it is git-ignored. If an audit finds a secret already in a context file, remove it, tell the user to rotate it, and do not echo the value.
- **Existing content is sacred in UPGRADE:** preserve wording and intent of user-authored policies; move and wire them, don't rewrite or silently drop them.
- **Shared `AGENTS.md`:** prefer `@./AGENTS.md` from the root `GEMINI.md` over changing `context.fileName` in settings (which is the user's configuration).
- **Valid frontmatter:** `paths` is a YAML list of glob strings in `rules/`; omit frontmatter in `standards/`, `GEMINI.md` and `scratchpad.md` (which has only the sync comment).
