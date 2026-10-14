---
id: 0001-harness-agnostic
intent: ./intent.md
status: draft
product_owner: Repository owner
technical_reviewer: Repository owner
risk: medium
skills_applied: [security-policy, compliance-policy]
generated_by: Coding task authorized by user; manual PR approval pending
date: 2026-10-14
---

# Spec: Harness-independent SDLC

## Requirements

| ID | Requirement | Traces to | Acceptance check |
|----|-------------|-----------|------------------|
| R1 | One canonical instruction/policy tree; generated vendor discovery files | Shared SDLC core | Drift checks and preserved hook regressions |
| R2 | Explicit adapters normalize prompts, permission modes, timeouts and results | Multi-harness adoption | Offline native/custom protocol tests; invalid results fail |
| R3 | Policy decisions are independent of native tool events | Shared controls | Canonical event tests and Claude translation regressions |
| R4 | Eval cases use portable modes/results and isolated checkouts | Consistent comparisons | Source checkout unchanged, exact commit recorded, failed execution cannot pass |
| R5 | Generic automation never invokes Claude directly | Shared CI/maintenance | Shared runner wired into review, triage, spec generation, evals and monitoring |
| R6 | Humans/agents can adopt a fresh project safely | Ease of adoption | English/Spanish guide, template/fork comparison, doctor and discovery index |
| R7 | Human approval and sandbox limits are explicit | Constraints | CODEOWNERS/governance updates, credentialed PR code never run automatically |

## Design
Canonical AGENTS.md/.agents; Python standard-library execution, policy and eval entry points;
Claude/Codex CLI adapters; versioned JSON command protocol for other CLI/SDKs. Vendor permissions
remain at adapter boundaries. CI/branch protection/deployment environments are authoritative.

## Policy conformance
### Security
Shell-free adapter argv, strict modes/results, process-group timeouts, normalized policy paths,
no bypass flags, no automatic credentialed evals on unreviewed PR code. Native/live authentication
is not inferred from offline tests. Heuristic hooks do not replace an OS sandbox.
### Compliance
Human gate ownership and source of truth remain explicit; no fabricated policy owner/approval.
### Brand
Existing repository language/style retained; Spanish adoption guide supports the requesting user.
### UX / accessibility
Documented copy-and-run setup and prerequisite diagnosis; no new application UI.

## Areas of concern

| # | Concern | Owner | Resolution |
|---|---------|-------|------------|
| 1 | Other harnesses have different discovery/permission APIs | Adopter/platform team | Command contract; no speculative native support claim |
| 2 | Credentials and trusted model evals need project configuration | Repository owner | Offline tests always run; manual/scheduled credentialed evals require reviewed refs |
| 3 | Final specification/plan approval | Repository owner | This PR is for manual review; documents are not marked approved by the agent |

## Approval
Pending human PR review. Implementation was requested directly by the user.
