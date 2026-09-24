---
incident: <INC-id>
date: <YYYY-MM-DD>
severity: <SEV1-4>
service_owner: <name>
status: draft            # draft | reviewed
---

# Post-mortem: <short title>

<!-- Blameless. Describe systems and decisions, not people. Name this file YYYY-MM-DD-<INC-id>.md. -->

## Summary
<!-- Two or three sentences: what happened, impact, how it ended. -->

## Impact
<!-- Users affected, duration, data, money, SLOs breached. -->

## Detection
<!-- Which band/alert/message caught it, when, and how long after it started. -->

## Timeline (UTC)
| Time | Event |
|------|-------|
| | |

## Root cause
<!-- The mechanism, with evidence (logs, commits, PRs). -->

## Resolution and verification
<!-- What restored service. Evidence the metric is back at baseline. -->

## What went well / what didn't

## Actions
| Action | Type (fix / eval / band / runbook / CLAUDE.md) | Owner | Link |
|--------|-------------------------------------------------|-------|------|
| Add regression eval `evals/incident-<id>.json` | eval | | |
