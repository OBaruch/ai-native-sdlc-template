---
name: compliance-policy
description: Apply regulatory and compliance requirements (e.g. GDPR, SOC 2, PCI DSS, HIPAA, sector rules). Use when a change stores, moves, exports or deletes personal or regulated data, changes retention, adds a data processor or third party, or touches audit trails and consent.
---

# Compliance requirements

Owner: `<compliance officer>` · Source of truth: `<link to the compliance register>` · Version: `<x.y>`

<!-- TEMPLATE: keep only the regimes that apply to you and replace the placeholders. -->

## Applicable regimes
- `<Regime A, e.g. GDPR>` — scope: `<which products / data>`
- `<Regime B>` — scope: `<...>`

## Requirements to check
1. **Lawful basis and purpose**: every new personal-data field states its purpose and basis.
2. **Data minimisation**: collect only what the stated outcome needs.
3. **Retention**: define how long the data lives and how it is deleted (`<retention schedule>`).
4. **Residency**: data stays in `<regions>`; no new cross-border transfer without approval.
5. **Third parties**: a new processor or SaaS needs a DPA / vendor review (`<process link>`).
6. **Audit trail**: regulated actions are logged immutably with actor and timestamp.
7. **Data subject rights**: the change keeps export and deletion working for `<systems>`.

## Output
In `spec.md`, add a **Compliance** subsection listing each requirement touched and how it is met.
Anything unclear or conflicting goes under **Areas of concern**, addressed to this policy's owner.
Never mark a requirement "not applicable" without saying why.
