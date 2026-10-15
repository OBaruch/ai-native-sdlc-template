---
description: Test-first bug fix; the failing test is committed before the fix and then protected
argument: <bug description or issue number>
---

Bug: {{arguments}}

Phase 1 (reproduce, no fix yet):
1. Write a test that reproduces the bug through the public behavior, not the internals.
2. Run it and confirm it fails **for the reason described in the bug**. Show the output.
3. Commit only the test: `test: reproduce <bug>`.
4. Stop and ask me to run `touch .agents/fix-task`. From then on, test files are read-only
   (enforced by `.agents/hooks/protect-tests.sh`).

Phase 2 (fix, after I confirm the marker is set):
5. Change the code, never the test, until the new test and the full suite pass.
6. Run `make check` and paste the output.
7. Summarize the root cause in two sentences. If this bug came from a production incident,
   draft the eval under `evals/` (see `evals/incident-0001-example.json`).
