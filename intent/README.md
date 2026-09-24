# intent/

The home of every change's artifact chain. One folder per change:

```
intent/NNNN-short-slug/
├── intent.md   # Plan    – what is wanted, why, constraints (originator + product owner)
├── spec.md     # Design  – requirements + design, policy conformance, areas of concern
└── plan.md     # Build   – files, order of work, risks, proof (engineer, plan mode)
```

`0000-template/` holds the templates. Copy it; never edit it for a real change.

## Lifecycle and triggers

| Artifact | Written by | Accepted by | Acceptance triggers |
|----------|-----------|-------------|---------------------|
| `intent.md` | Originator with Claude (`/new-intent`), or the monitoring loop | Product owner merges the PR (closing it = rejected) | `intent-to-spec` workflow opens a PR with `spec.md` |
| `spec.md` | Claude (`/write-spec` or the workflow) | Product owner (+ tech lead if high risk) | Plan mode (`/write-plan`) |
| `plan.md` | Claude in plan mode, iterated with the engineer | Engineer (tech lead/architect if high risk) | Implementation, then PR review against spec + plan |

Git history is the audit trail: author, timestamps and approvals for each file.

## Source of truth
If a legacy tool (Jira, ServiceNow, a requirements tool) also tracks the change, fill
`record_id` in the frontmatter and put this folder's commit SHA in the legacy record.
See `governance/source-of-truth.md`.
