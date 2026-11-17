# Delegating large repositories to subagents

Read this when `scan_repo.py` prints `DELEGATION: REQUIRED`, or when you judge a repo too large to read inline. The goal: raw source never enters the main context. Subagents read; the main agent only receives short digests and does the synthesis.

## Contents
1. When to delegate
2. Partitioning
3. Launching subagents
4. Subagent brief (copy/paste)
5. Digest schema
6. Synthesis and verification
7. Fallback without subagents
8. Using the same pattern in SYNC mode

## 1. When to delegate

`scan_repo.py` triggers delegation at any of: 800+ files, ~80k source LOC, or 6+ package roots. Treat these as defaults. Delegate earlier if the repo is polyglot or you already feel the context filling; skip delegation for small repos where a subagent's startup cost exceeds the reading.

## 2. Partitioning

Use the script's partitions (balanced to ~40k LOC each, split along directory boundaries, small siblings packed together). Adjust by hand when:
- a partition is flagged `OVERSIZE` (flat directory too big): split it by sub-feature or file groups;
- a natural unit is cut in half (a package should stay whole; shared libs used by many partitions deserve their own partition).

Always add one extra partition for **repo-level concerns** that live outside source dirs: root manifests, CI/CD, infra (`terraform/`, `k8s/`), docs, scripts, env examples.

Cap total partitions at ~12. If more, merge the smallest.

## 3. Launching subagents

- Launch all partitions **in parallel in one message** (one Task/subagent call per partition), in batches of at most 6-8 at a time.
- Subagents are **read-only**: they must not write, edit or run anything that changes the repo. Tell them so in the brief.
- Use a lighter/faster model for exploration when the platform lets you choose; synthesis stays with the main agent.
- Subagents do not share memory. Everything they need goes in the brief.

## 4. Subagent brief (copy/paste, fill the placeholders)

```
You are analyzing ONE partition of a repository to help build Claude Code context files.
Read-only: do not modify files or run commands that change state.

Repo root: <ABS_PATH>
Your partition: <PATHS>
Repo-wide facts (for orientation): <1-3 lines: topology, main stack>

Explore your partition: manifests, entry points, public interfaces, a representative sample of files per sub-directory, tests, configs. Prefer reading over guessing; every claim must be backed by a file path you actually opened.

Return ONLY the digest below, max 60 lines, no preamble. Use "unknown" instead of guessing.
<DIGEST SCHEMA>
```

## 5. Digest schema

```
## <partition name>  (<paths>)
- Purpose: one sentence
- Entry points: file paths
- Stack & key libs: with versions when a manifest states them
- Modules (<=8): path - responsibility
- Depends on / used by: other partitions or external services
- Data & contracts: DB models, API routes, events/queues, shared types
- Conventions observed: each with an example file path
- Testing: framework, location, naming, notable gaps
- Commands: build / test / lint / run, as found in manifests or scripts
- Gotchas: generated code, legacy zones, do-not-touch, tricky config
- Suggested scoped CLAUDE.md: yes/no (+ where) and why
- Suggested path rules: glob -> rule, only if a distinct convention exists
- Key files read: <=10 paths
```

## 6. Synthesis and verification

1. Merge digests into one picture: topology, module map, cross-partition dependencies, data flow, contradictions between digests (e.g. two partitions claiming different test frameworks).
2. Deduplicate conventions: if 3+ partitions share a convention it is a repo-wide standard/rule; otherwise it belongs to a scoped `CLAUDE.md` or rule.
3. **Spot-check**: open 3-5 files cited as evidence, prioritizing surprising or high-impact claims (security, data model, commands). Subagents can misread; a wrong command in `CLAUDE.md` costs every future session.
4. Resolve `unknown`s only if they affect generated content; otherwise record them in `scratchpad.md` under Open questions.
5. Feed the merged result into the standards interview (Step 3): use detected tooling to offer realistic defaults.

## 7. Fallback without subagents

If no subagent tool exists (e.g. plain chat), process partitions sequentially but keep the main context lean: for each partition, read selectively, immediately write its digest (same schema) to a scratch file such as `/tmp/ctx-digests/<n>.md`, then drop the raw reading from your reasoning. Build everything afterwards from the digest files only. Tell the user the analysis ran sequentially and may take longer.

## 8. Using the same pattern in SYNC mode

When `detect_drift.py` reports changes spread over many areas, delegate only the **affected** partitions (changed directories + their neighbors), asking each subagent to compare current code against the existing `CLAUDE.md`/rules/standards for that area and return a list of stale or missing statements instead of a full digest.
