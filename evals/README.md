# Harness-independent agent evaluations

Evals exercise the agent's instructions, policy skills, adapter and model. The same task
and acceptance checks run against any configured adapter. No native transcript field or
Claude tool string is required; all results use `.agents/contracts/result.schema.json`.

1. Collect 20–50 real tasks with known accepted outcomes.
2. Copy an example, replace its prompt/checks, specify portable `mode` and `timeout_seconds`, and enable it.
3. After an incident, add an owned incident eval permanently.
4. Run identical cases for each selected adapter before activating automation.

```bash
SDLC_AGENT_ADAPTER=codex make evals
bash evals/run.sh --adapter claude --adapter codex --require-enabled
EVAL_FILTER='evals/incident-*.json' bash evals/run.sh --require-enabled
EVAL_PASS_THRESHOLD=0.95 make evals
```

Each case/adapter starts from its exact `base_ref` commit in a disposable local clone.
The original checkout, working changes and worktree registry remain untouched. Only committed
base contents are evaluated: commit the candidate first, or use a maintainer-approved candidate
ref in the workflow. Configure the command adapter executable using an absolute path if it
lives outside that commit. Temporary clones are removed even after a failure.

| Check | Passes when |
|-------|-------------|
| `{"run": "command"}` | A trusted acceptance command exits 0 in the disposable clone |
| `{"result_field": "is_error", "equals": false}` | The normalized result has that field and value |

The runner also requires a successful agent exit; permissive grading cannot mask execution
failure. Thresholds compare the actual fraction, without rounding it into a pass. Malformed
cases/thresholds fail, disabled cases are reported separately, and zero enabled cases is
SKIPPED. `--require-enabled` rejects zero-case suites; CI uses it.

Results and an exact-commit summary are saved in a unique `evals/.runs/<run-id>/` directory;
`evals/.runs/summary.md` points humans to the latest summary. Do not commit these artifacts.
Acceptance commands are trusted repository code, not a model-generated script. Enabled evals
may invoke a paid model and need only that adapter's credentials.

PRs run offline adapter and policy regression tests without model secrets. Credentialed evals
run on schedule or a maintainer's workflow dispatch for a reviewed ref; do not execute
unreviewed PR grading commands with credentials. A skipped PR eval job is not G5 evidence.
The examples are disabled because this scaffold has no application endpoints yet.
