# Standards interview

The interview is what makes `.claude/standards/` reflect the team's intent instead of just the current code. Always run it in INIT mode, after the scan and before writing standards.

## Contents
1. How to run it
2. Core questions (always ask)
3. Conditional questions (ask when the scan shows the area exists)
4. Turning answers into files
5. Re-asking in SYNC mode
6. Pre-filled interview in UPGRADE mode

## 1. How to run it

- Ask **after** the scan so options can include what the repo already does, marked "(detected)" and listed first as the recommended default.
- Use the interactive question tool when available (`AskUserQuestion` in Claude Code). It takes up to 4 questions per call with 2-4 options each, and the user can always type a custom answer. Otherwise use a short numbered list and accept replies like "1b, 2a, 3 custom: ...".
- Round 1: the four core topics (A-D). Round 2: workflow/autonomy (E) plus the conditional topics that apply. Do not drown the user: 8-10 questions total is plenty.
- Always finish with one free-text question: "Anything else Claude must always or never do in this repo?"
- If the user says "you decide" for a topic, pick the scan-derived default, write it, and mark it `(assumption - confirm)` in the standard.
- If the user gives a free-form answer to a question, quote their intent faithfully; do not "improve" it into something else.

## 2. Core questions (always ask)

### A. Code style & documentation  ->  `code-style.md`
- **Comments/docstrings:** none unless non-obvious / only public APIs and exported functions / everything documented / follow existing (detected).
- **Typing:** strict types required / gradual / not applicable.
- **Naming & structure:** follow detected linter config / custom rules (ask which) .
- **Size limits:** soft limits on file or function length? (none / ~300-line files / custom)
- **Error handling:** exceptions vs result types, custom error classes, never swallow errors?
- **Comment language:** English / Spanish / follow existing.

### B. Testing  ->  `testing.md`
- **Test types required:** unit / integration / e2e / contract (multi-select).
- **Framework & layout:** detected framework; co-located vs `tests/` folder.
- **Coverage:** no threshold / soft target (ask %) / enforced in CI.
- **Process:** write tests with every change / TDD / only for bugfixes and critical paths.
- **Mocking:** what may be mocked (network, DB, time) and what must hit real implementations.
- **Must tests pass before Claude says "done"?** always / only affected / no.

### C. API  ->  `api-design.md` (skip only if the repo exposes no API)
- **Style:** REST / GraphQL / gRPC / tRPC / mixed.
- **Error format:** standard envelope (ask shape, e.g. RFC 7807 problem+json) / per-service.
- **Versioning:** URL / header / none.
- **Validation:** which library or layer validates input (Zod, Pydantic, class-validator...).
- **Pagination, naming, status-code rules, idempotency** if relevant.
- **Documentation:** OpenAPI/Swagger kept in sync? generated or hand-written?

### D. Security  ->  `security.md`
- **Secrets:** env vars only / secret manager (which) / never touch `.env*`.
- **AuthN/AuthZ:** mechanism (JWT, sessions, OAuth) and where checks must live (middleware, service layer).
- **Input & output safety:** parameterized queries only, output encoding, file upload rules.
- **PII & logging:** what must never be logged; data-retention or compliance regimes (GDPR, LFPDPPP, HIPAA, PCI, SOC2...).
- **Dependencies:** policy for adding packages (ask first / allowed if popular and maintained / pinned versions / audit in CI).
- **Hard prohibitions:** anything Claude must never do (e.g. disable auth, commit keys, touch prod config).

## 3. Conditional questions

Ask only when the scan finds the corresponding area.

### E. Workflow & autonomy  ->  `git-and-workflow.md` (always ask in round 2)
- **Commits:** Conventional Commits / ticket-prefixed / free-form. Language of messages.
- **Branching & PRs:** trunk-based / gitflow; PR size and template expectations.
- **Autonomy:** what Claude may do without asking - install dependencies, run migrations, run the full test suite, edit CI files, push, open PRs. Record as explicit allow / ask-first / never lists.
- **Definition of done:** lint + types + tests green? docs/changelog updated?

### Database & migrations  ->  `database-and-orm.md`
Migration tool and rules (never edit applied migrations, reversible only), naming, seed data, who may run migrations, raw SQL policy, N+1 awareness.

### Frontend  ->  `frontend.md` / `design-system.md`
Component conventions, state management approach, styling system, accessibility level (WCAG target), i18n, browser support, performance budgets.

### Observability & errors  ->  `observability.md`
Logging library and levels, structured fields, tracing/metrics, alert-worthy conditions, error-reporting service.

### Infra & CI/CD  ->  `infra.md`
IaC conventions, environments, what changes need human review, deployment flow, cost-sensitive resources.

### Performance, concurrency, async jobs  ->  `async-workers.md` / `performance.md`
Queue/worker rules, retries and idempotency, timeouts, caching policy, perf budgets.

### Monorepo specifics
Cross-package import rules, who owns shared libs, versioning/release process, affected-only test commands.

## 4. Turning answers into files

- One standard per topic; do not merge unrelated topics to save files.
- Each file starts with: `> Source: decision (interview YYYY-MM-DD)`; add `| observed (scan)` for parts taken from the repo.
- Write rules as short imperative statements Claude can follow ("Never log request bodies"), not essays. Put a "Why" only where the reason is non-obvious.
- Add a brief **Verification** line when the standard is checkable (`run npm run lint && npm test before finishing`).
- Mark unconfirmed items: `(assumption - confirm)`.
- Decide where each standard is imported: global and short -> root `CLAUDE.md`; area-specific -> scoped `CLAUDE.md`; file-type-specific -> mention from the matching rule.

## 5. Re-asking in SYNC mode
6. Pre-filled interview in UPGRADE mode

Do not repeat the whole interview. Ask only about **new** areas that appeared (a new database, a new API surface, a new test framework) or when observed reality contradicts a `decision` standard. Offer three options: update the standard to match the code, keep the standard (code is wrong), or mark the area as an exception.

## 6. Pre-filled interview in UPGRADE mode

When the repo already has context files, the interview becomes **confirm + fill gaps**, not a blank questionnaire:

1. **Confirm (one batched question):** list the policies you extracted per topic (e.g. "Testing: Jest, every function needs a test; Security: never log PII...") and ask whether they are still accurate. Options per topic: "Yes, keep" / "Needs changes (I'll tell you)" / "Drop it". Corrections the user gives replace the extracted text.
2. **Fill gaps:** for each core topic (A-E) with no or thin coverage in the existing files, ask the normal questions from section 2/3, with the detected defaults listed first.
3. Extracted and confirmed policies get `> Source: decision (migrated from <file>, YYYY-MM-DD)`; new answers get `> Source: decision (interview YYYY-MM-DD)`.
4. If the user declines to answer a gap, write scan-derived defaults marked `(assumption - confirm)`.
