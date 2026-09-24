---
id: NNNN-short-slug
intent: ./intent.md
status: draft            # draft | approved | superseded
product_owner: <Name>
technical_reviewer: <Name, required when risk is high>
risk: low                # low | medium | high (per governance/approval-gates.md)
skills_applied:          # name@version of every policy skill used to produce this spec
  - security-policy@<x.y>
  - compliance-policy@<x.y>
  - brand-guidelines@<x.y>
  - ux-standards@<x.y>
generated_by: <"/write-spec" or "intent-to-spec workflow run <url>">
date: <YYYY-MM-DD>
---

# Spec: <title>

## Summary
<!-- Two or three sentences: what will be built and why, traceable to intent.md. -->

## Requirements
<!-- Numbered, testable. Each one traces to the intent's problem or outcome. -->
| ID | Requirement | Traces to | Acceptance check |
|----|-------------|-----------|------------------|
| R1 | | Problem / Outcome | |

## Design
### Integration with the existing system
<!-- Components, APIs, data flow, where it plugs into the current codebase. -->

### Data
<!-- New or changed fields, classification, retention. -->

### User experience
<!-- Flows, screens, states. Link the approved mock if there is one. -->

## Policy conformance
<!-- One subsection per applied skill: which rules the change touches and how they are met. -->
### Security
### Compliance
### Brand
### UX / accessibility

## Open questions from the intent
<!-- Each one answered here, or carried forward with an owner. -->

## Areas of concern
<!-- Conflicting or unsatisfiable policies, ambiguities, risks. Each item names the owner who must decide. Resolve these before engineering starts. -->
| # | Concern | Policy / source | Owner | Resolution |
|---|---------|-----------------|-------|------------|
| 1 | | | | open |

## Approval
<!-- Product owner (and technical lead for high risk) records the decision here or on the PR. -->
