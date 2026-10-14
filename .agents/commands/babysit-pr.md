---
description: Drive a PR the agent opened to green; address unresolved review comments and failing checks until only code-owner approval remains
argument: <PR number>
---

PR: #{{arguments}}

Loop until the PR is green and waiting only on human approval (max 5 rounds):

1. `gh pr view {{arguments}} --comments` and `gh pr checks {{arguments}}` to collect unresolved
   review comments and failing checks.
2. For each failing check, read its log (`gh run view <id> --log-failed`), find the cause and fix it.
3. For each unresolved comment, make the change or reply explaining why not. Never dismiss a
   comment silently.
4. Run `make check` locally, then commit and push to the PR branch.
5. If a reviewer flags the same kind of mistake a second time, add the correction to
   `AGENTS.md > Recurring agent mistakes` in this PR.

Never approve or merge the PR, never force-push over someone else's commits, and stop to ask
if a comment requires a product or policy decision.
