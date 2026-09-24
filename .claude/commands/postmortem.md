---
description: Write a blameless post-mortem, add the lesson and draft the regression eval for an incident
argument-hint: <incident id>
---

Incident: $ARGUMENTS

1. Gather the timeline from the incident channel, alerts, deploys and PRs you can reach
   (MCP / `gh`). Ask me for anything you cannot access.
2. Write `postmortems/YYYY-MM-DD-$ARGUMENTS.md` from `postmortems/TEMPLATE.md`. Keep it blameless.
3. Confirm the metric is back at baseline and include the evidence.
4. Add one line to `postmortems/LESSONS.md`.
5. Draft a regression eval in `evals/incident-$ARGUMENTS.json` owned by the team that owned the incident.
6. For follow-up work bigger than a small fix, write an `intent.md` (use `/new-intent`).
