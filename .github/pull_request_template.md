## Change
<!-- One or two sentences. -->

**Artifact chain:** `intent/NNNN-slug/` — [intent](../intent/NNNN-slug/intent.md) · [spec](../intent/NNNN-slug/spec.md) · [plan](../intent/NNNN-slug/plan.md)
**Legacy record (if any):** <!-- e.g. JIRA-123 -->
**Risk class:** low / medium / high <!-- governance/approval-gates.md -->

## Verification evidence
<!-- Paste the literal output (tail) of the commands, or link the CI run. -->
```
make lint:
make test:
make build:
```
- [ ] UI changes: screenshot attached and compared with the approved mock
- [ ] Bug fix: the reproducing test was committed before the fix and is unchanged

## Plan conformance
- [ ] The diff matches `plan.md`, or `plan.md` was updated in this PR
- [ ] No tests, hooks, CI checks or policy skills weakened (or explained below)
- [ ] `CLAUDE.md` updated if this PR corrected a repeated agent mistake

## Notes for the reviewer
<!-- Where to focus: intent and risk. Mechanical checks are already attached above. -->
