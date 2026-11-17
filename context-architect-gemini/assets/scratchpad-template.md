<!-- context-sync
last_synced_commit: none
last_synced_at: none
generated_by: context-architect-gemini
-->
# Scratchpad - <Project name>

Living architecture notes for Gemini and humans. Updated on every structural change (see "Context maintenance" in GEMINI.md). Keep under ~200 lines; push detail into `standards/` or scoped `GEMINI.md` files.

## System overview
<What the system does, main users/flows, deployment shape in 4-6 lines.>

## Stack
- Languages/runtime: <...>
- Frameworks: <...>
- Data stores / external services: <...>
- Tooling: <lint, test, build, CI>

## Module map
| Path | Responsibility | Depends on | Notes |
|---|---|---|---|
| `apps/api/` | <...> | `packages/db` | scoped GEMINI.md |

## Data flow & contracts
<Request/event lifecycle, key API routes or events, queues, shared types. A small mermaid or ASCII diagram is fine.>

## Entry points
- <path> - <what starts here>

## Key decisions
- <decision> - <why / date>

## Hazards & gotchas
- <generated code, legacy zones, fragile config, do-not-touch areas>

## Open questions / assumptions
- <things the scan could not confirm>

## Change log
<!-- newest first; keep ~15 entries, fold older ones into "Earlier history" -->
- YYYY-MM-DD: Initial architecture scan.
