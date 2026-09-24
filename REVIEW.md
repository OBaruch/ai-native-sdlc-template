# Review policy

<!--
TEMPLATE — owned by the tech lead. Read by the Claude review workflow on every PR
(.github/workflows/claude-code-review.yml) and by human reviewers.
Tune monthly: rate the findings, adjust the nit cap, extend "Out of scope".
-->

Owner: `<tech lead name / @handle>` · Last tuned: `<YYYY-MM-DD>`

## Passes
Review every PR in the passes below and tag each finding with its pass name.

1. **Correctness** — logic errors, unhandled edge cases, race conditions, regressions in behavior that is not part of the change.
2. **Security** — injection, missing authentication or authorization, secrets or PII in code, logs or error messages, unsafe deserialization, over-broad permissions.
3. **Conformance** — does the diff do what `intent/<change>/spec.md` asks and follow `plan.md`? Flag files changed that the plan does not mention, and plan steps with no matching change. Check it against our design principles:
   - `<principle 1, e.g. domain logic never imports from adapters>`
   - `<principle 2>`
4. **Guardrails** — the change must not weaken tests, hooks, CI checks, `CLAUDE.md` or skills without saying why in the PR description. Flag it when a change makes `CLAUDE.md` outdated.

## Severity
- **Important** — would break behavior, lose or leak data, or breach a written policy. Must be fixed or explicitly accepted by a code owner.
- **Nit** — style, naming, minor readability. Never blocks.

## Limits
- At most `5` nits per review; summarize the rest as a count.
- Post findings as inline comments on the relevant line, plus one summary comment with the severity tally, for example `Important: 1 · Nit: 3`.

## Out of scope
- Generated code under `src/gen/`.
- Formatting and lint rules that CI already enforces.
- `<other paths or concerns to skip>`

## Human approval
Findings inform, they do not approve. Merging requires a code owner approval (`.github/CODEOWNERS`) through branch protection. Claude never approves its own PRs.
