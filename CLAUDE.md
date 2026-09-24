# <Project name>

<!--
TEMPLATE — replace every <placeholder>, then delete this comment.
Keep this file under one page: Claude reads all of it at the start of every session.
Working rule: when Claude makes the same mistake twice, add the correction under
"Things Claude gets wrong" (in the same PR where the mistake was caught).
-->

## Commands
- Build: `make build` — healthy output ends with `<e.g. BUILD SUCCESSFUL>`
- Test: `make test` (unit) — healthy output: `<e.g. 128 passed in 4.2s>`
- Integration: `make itest` — `<prerequisites, e.g. needs Docker running>`
- Lint: `make lint` — healthy output: `<e.g. 0 problems>`
- Run locally: `make run` — serves on `<http://localhost:8080>`

## Verifying your work
- Run `make lint`, `make test` and `make build` before reporting any task complete, and paste the output.
- All three must pass. Never skip, weaken or delete a failing test: fix the code, not the test.
- UI changes: screenshot the result and compare it with the approved mock; iterate until it matches.
- Bug fixes: the failing test is written and committed first, then `.claude/fix-task` is created and test files become read-only.

## How work flows here
- Each change lives in `intent/NNNN-slug/`: `intent.md` → `spec.md` → `plan.md`.
- Start non-trivial work in plan mode. The approved plan is committed as `plan.md`; if the implementation departs from it, update `plan.md` in the same commit.
- PRs link their intent, spec and plan, and are reviewed against `REVIEW.md`.

## Conventions
- Language / runtime: `<e.g. TypeScript 5, Node 22>`
- `<Domain rule, e.g. money is always a decimal type, never a float>`
- `<Testing rule, e.g. every endpoint has an integration test>`

## Architecture
- `src/` — `<what lives where, one line per top-level module>`
- `src/gen/` — generated code. Never edit by hand; change the generator or schema.

## Things Claude gets wrong
- `<e.g. Do not bump dependency versions; the platform team owns them.>`
