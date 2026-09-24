# Runbook: quarantine-flaky-test

Status: **pre-approved**, delivered as a pull request only (never pushed to the default branch).
Owner: `<platform team>`

## When
The CI failure rate breaches 3σ and the failures concentrate on one test that also passes on
re-run with the same commit (flaky rather than broken).

## Steps
1. Identify the test from `gh run view <id> --log-failed` across the failing runs.
2. Confirm it is flaky: the same commit has both passing and failing runs of that test.
3. Mark it quarantined with `<your framework's skip/quarantine marker>` and a comment linking the
   tracking issue. Never delete the test.
4. Open a PR labelled `maintain-loop` + `flaky-test`, with the evidence (run ids, pass/fail counts).
5. Create a tracking issue assigned to the test's code owner to fix and un-quarantine it.

## If it is not flaky
If the test fails consistently, it is a real regression: open a revert PR for the commit that
introduced it instead, and let the review gate decide.
