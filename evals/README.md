# evals/

Regression tests for the **agent's configuration**: `CLAUDE.md`, skills, hooks, subagents and
the model. The suite runs in CI (`.github/workflows/agent-evals.yml`) on every change to that
configuration and nightly, and a drop below the pass-rate threshold blocks the merge.

## Building the suite
1. Collect 20–50 real tasks from recent work whose accepted outcome you know.
2. Write one JSON file per task (copy `0001-example-task.json`): the prompt plus the checks that
   define "acceptable" (tests pass, lint clean, behavior unchanged, policy followed).
3. Set `"enabled": true`.
4. After every production incident, the owning team adds `incident-<id>.json`. It stays forever.
5. Retire cases that no longer discriminate between good and bad configurations and add new ones.

## Running
```bash
make evals                          # all enabled evals
EVAL_FILTER='evals/incident-*.json' make evals
EVAL_PASS_THRESHOLD=0.95 make evals
```
Results go to `evals/.runs/` (git-ignored); `summary.md` is also published to the CI job summary.

## Check types
| Check | Passes when |
|-------|-------------|
| `{"run": "<cmd>"}` | the command exits 0 inside the eval's worktree |
| `{"result_field": "is_error", "equals": false}` | the field in Claude's JSON result matches |
