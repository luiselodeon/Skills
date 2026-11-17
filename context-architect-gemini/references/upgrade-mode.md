# UPGRADE mode: bring an existing context setup up to best practices

Use this when the repo already has some agent context (a `GEMINI.md` from `/init` or hand-written, a `.gemini/` folder, `CLAUDE.md`/`.claude/`, `AGENTS.md`, `.cursorrules`...) but it is monolithic, uses the wrong import syntax, lacks rules/standards/imports, has rules nothing loads, or was written for another tool. The goal is a better structure **without losing anything the team wrote**.

## Contents
1. UPGRADE vs. SYNC vs. INIT
2. Principles
3. Target state (best-practices checklist)
4. Procedure
5. Transformation recipes
6. What not to do

## 1. UPGRADE vs. SYNC vs. INIT

- **INIT**: nothing exists. Build from the scan.
- **UPGRADE**: something exists, but its *structure or quality* is below best practice (no `@./imports`, no rules, giant root file, legacy syntax, unwired rules, duplicated text, other-tool files, secrets). Content mostly stays; where it lives changes.
- **SYNC**: structure is fine, but *content went stale* because the repo changed.

An upgrade usually ends with a SYNC baseline stamp, so the repo continues in SYNC mode afterwards. If the audit finds both structural gaps and stale facts, do UPGRADE first and fix the stale facts during the same pass.

## 2. Principles

1. **Lossless by default.** Every instruction in the existing files must end up somewhere (kept, moved, merged) or be on an explicit "proposed deletions" list the user approves. Never silently drop.
2. **Safety net first.** Before touching anything: if git, ensure a clean tree or suggest a branch/commit (`git switch -c chore/gemini-context-upgrade`); if not git, copy the existing context files to `.gemini-context-backup/` and tell the user.
3. **Existing text = the team's voice.** User-written policy is treated as `Source: decision (migrated)`. Keep its wording and intent; tighten only for clarity.
4. **Facts get verified, decisions get preserved.** Check factual statements (commands, paths, versions) against the repo and fix the wrong ones; do not "correct" opinions.
5. **Least surprise.** Show the plan (findings, routing table, before/after tree) and get approval before writing, unless the user said to just do it. Never touch `.gemini/settings.json`, hooks or permissions as part of an upgrade without separate consent.
6. **Scope to what's needed.** If the audit says a part is already good, leave it alone.

## 3. Target state (best-practices checklist)

Each line maps to audit finding ids from `scripts/audit_context.py`.

| Best practice | Finding id when violated |
|---|---|
| Root `GEMINI.md` exists, ~120 lines (<200 hard cap), with identity, architecture summary, verified commands, directory map | `NO_ROOT_GEMINI`, `ROOT_TOO_LONG`, `NO_COMMANDS` |
| Shared knowledge lives once, in `standards/`, imported with `@./path.md` | `NO_STANDARDS_DIR`, `INLINE_STANDARD`, `NO_IMPORTS`, `DUPLICATED_CONTENT` |
| Correct import syntax: `@./path/file.md` or `@../x.md`, relative to the importing file, `.md` targets only | `LEGACY_IMPORT_SYNTAX`, `IMPORT_STYLE`, `NON_MD_IMPORT`, `BROKEN_IMPORT` |
| File-type/area conventions are rules with valid `paths:` that match real files | `NO_RULES_DIR`, `INLINE_RULE_CANDIDATE`, `RULE_FRONTMATTER`, `STALE_GLOB` |
| **Every rule is wired** (Rules index in root, or imported by a scoped `GEMINI.md`) | `UNWIRED_RULE` |
| Each package/major area has a scoped `GEMINI.md` importing only what it needs | `NO_SCOPED_GEMINI`, `LARGE_DIR_NO_GEMINI` |
| Root loads little on every prompt (imports stay short and global, chains shallow) | `ROOT_LOADS_TOO_MUCH`, `IMPORT_TOO_DEEP` |
| `scratchpad.md` exists with sync baseline; root has the Context maintenance block | `NO_SCRATCHPAD`, `NO_SYNC_BASELINE`, `NO_MAINTENANCE_BLOCK` |
| Standards carry provenance (`> Source:`) | `STANDARD_NO_PROVENANCE`, `ORPHAN_STANDARD` |
| No secrets, no machine-specific paths, no vague filler | `SECRET_IN_CONTEXT`, `ABSOLUTE_PATHS`, `VAGUE_INSTRUCTIONS`, `DANGLING_PATH` |
| Other tools' agent files integrated, existing docs referenced not copied | `LEGACY_NOT_INTEGRATED`, `DOC_NOT_REFERENCED` |
| `.gemini/.env` (API keys) is git-ignored | `ENV_FILE_NOT_IGNORED` |

## 4. Procedure

**Step 0 - Safety net.** See principle 2.

**Step 1 - Audit.** Run `python <skill>/scripts/audit_context.py <root>` (score, findings by severity) and `scan_repo.py` (repo facts; delegate if it says so, see `subagent-delegation.md`). Share the score and the top findings with the user in plain language.

**Step 2 - Inventory existing content.** Read every context file in full (`GEMINI.md` files, rules, standards, `scratchpad.md`, plus legacy files such as `CLAUDE.md`, `.claude/`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.cursor/rules/*`). Build a **routing table** with one row per section or group of instructions:

| Source (file > section) | Kind | Destination | Action |
|---|---|---|---|
| `GEMINI.md > Testing` | policy | `standards/testing.md` | move |
| `GEMINI.md > React components` | file-type convention | `.gemini/rules/react-components.md` (`apps/web/**/*.tsx`) + wiring | move |
| `GEMINI.md > Deploy` | fact | `scratchpad.md` + root commands | move + verify |
| `.cursorrules` line 4 | duplicate of testing | - | merge |
| `GEMINI.md` line 2 ("write clean code") | vague | - | propose delete |

Kinds: **fact** (verify against repo), **policy** (a decision, preserve), **file-type convention** (rule, and decide how it is wired), **folder-specific** (scoped `GEMINI.md`), **cross-cutting topic** (standard), **vague/obsolete/duplicate** (merge or propose deletion with evidence).

**Step 3 - Gap interview (standards).** Do not restart from zero, but do not skip. Run in two moves, per `standards-questionnaire.md` section 6:
1. *Confirm* what was extracted: "I found these policies in your files: testing = X, security = Y... still accurate?" (one batched question).
2. *Fill gaps* for core topics that the existing content does not cover (code style/docs, testing, API, security, workflow/autonomy) plus any conditional area the scan found.

**Step 4 - Plan and approval.** Present: audit score and key findings, the routing table (with the proposed-deletions list called out), a before/after tree of context files, how each rule will be wired, and which items are assumptions. Wait for approval.

**Step 5 - Apply, in this order** (so imports always point to files that already exist):
1. `standards/*.md` (provenance header on each; migrated policy => `> Source: decision (migrated from <file>, YYYY-MM-DD)`).
2. `.gemini/rules/*.md` (frontmatter `paths:`; verify each glob matches real files before saving).
3. Scoped `GEMINI.md` files (compute relative import depth carefully; import the folder-bound rules here).
4. Slim the root `GEMINI.md`: identity, architecture summary, verified commands, directory map, short global `@./imports`, **Rules index** for cross-cutting rules, scratchpad pointer, Context maintenance block.
5. `scratchpad.md` from the template, filled from the scan; fold relevant architecture notes found in old files.
6. Legacy-file integration (recipes below).

**Step 6 - Verify.**
1. **Lossless check:** walk the routing table; confirm each row's content exists at its destination (or is on the approved deletions list). Report any miss and fix it.
2. Run `detect_drift.py <root>` (broken/non-md imports, unwired rules, stale globs, dangling paths, sizes) and fix everything it reports.
3. Run `audit_context.py <root>` again. Aim for no high findings and a clearly better score; explain any remaining ones (e.g. a legacy file the user wants to keep).
4. Run `detect_drift.py <root> --stamp` to set the SYNC baseline.
5. Ask the user to run `/memory show` (and `/memory reload` first if a session is already open) to see the context Gemini actually receives.

**Step 7 - Report** in the user's language: score before -> after, what moved where, what was deleted (with approval), assumptions to confirm, and how to keep it current (SYNC mode, optional hook/command from `sync-mode.md` section 7, offered but not installed unasked).

## 5. Transformation recipes

- **Wrong import syntax** (`@import path`, bare `@path/file.md`, Claude-style imports) -> `@./path/file.md` on its own line, path relative to the file; re-verify it resolves. Imports of non-`.md` files cannot work: replace with a plain pointer or convert the target to `.md`.
- **Monolithic root file** (including a generic file produced by `/init`) -> split by section kind (routing table). Root keeps identity/commands/map/Rules index/imports only.
- **Topic section** (testing, security, API, style, workflow, DB...) -> `standards/<topic>.md`, wording preserved, provenance header, then import it from the narrowest `GEMINI.md` that needs it (root only if global and short).
- **File-type section** ("React components must...", "migrations are...") -> `.gemini/rules/<name>.md` with `paths:` derived from real files (`git ls-files` / `scan_repo.py`), quoted when starting with `*` or `{`. Keep a one-line pointer to the matching standard if one exists. Then wire it: folder-bound -> import from that folder's scoped `GEMINI.md`; cross-cutting -> row in the root Rules index.
- **Folder-specific section** -> that folder's scoped `GEMINI.md`. Relative import depth = folder depth.
- **Same text in several files** -> keep the best-worded copy in one place (standard or rule) and import/reference it from the rest.
- **`CLAUDE.md` + `.claude/`** -> migrate as above: `CLAUDE.md` sections via the routing table; `.claude/rules/*.md` -> `.gemini/rules/` (keep the `paths:` frontmatter, then **add the wiring Claude Code did implicitly**); `.claude/standards/` -> `standards/`; Claude-style `@path` imports -> `@./path`. Leave the originals in place unless the user wants them removed, and never touch `.claude/settings.json`, hooks, commands or permissions (they do not translate automatically; mention it in the report). `CLAUDE.local.md` is personal: do not migrate it, suggest `~/.gemini/GEMINI.md` for personal preferences instead.
- **`AGENTS.md`** (shared across tools) -> do not duplicate. Prefer `@./AGENTS.md` from the root `GEMINI.md` and add only Gemini-specific content around it. If it is tiny or stale, migrate instead. Changing `context.fileName` in settings is an alternative, but it edits user configuration, so ask first.
- **`.cursorrules`, `.cursor/rules/*`, `copilot-instructions.md`** -> migrate still-valid rules into standards/rules; mention in the report that the originals remain for those tools.
- **Existing docs** (`CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/`) -> reference from root `GEMINI.md`: `@./CONTRIBUTING.md` if short (<~100 lines) and `.md`, a plain pointer ("see `ARCHITECTURE.md` before cross-module work") if long. Never paste them in.
- **Secrets found** -> remove the value, keep the variable name if useful, tell the user plainly to rotate the credential since it lived in a repo file/history. Do not echo the value in chat.
- **Absolute/machine paths** -> repo-relative.
- **Vague filler** ("follow best practices", "write clean code") -> propose deletion, or replace with the concrete rule it was gesturing at if one is evident from the repo.
- **`.gemini/.env` visible to git** -> ask, then add to `.gitignore` and advise rotating the key if it was committed.
- **Stale facts** found during inventory (wrong commands, removed folders) -> fix with evidence from the repo and list each correction in the report.

## 6. What not to do

- Do not rewrite wording of policies to "sound better" or change their meaning.
- Do not delete the user's legacy files or old content without approval.
- Do not invent standards the user never expressed to fill the structure; use the interview, or mark `(assumption - confirm)`.
- Do not move content into `standards/` or `.gemini/rules/` without wiring it (import or Rules index); orphans are findings and, for Gemini CLI, simply never load.
- Do not import many standards from the root to look "organized"; that defeats the token savings.
- Do not modify `.gemini/settings.json`, hooks, or permissions during an upgrade without explicit separate consent.
