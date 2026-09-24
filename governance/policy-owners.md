# Policy owners

Every skill that encodes a policy has a named owner and a written source of truth. The owner
signs off on every change to the skill (enforced by `.github/CODEOWNERS`).

| Skill | Policy | Owner | Source of truth | Version | Enforcement behind the skill |
|-------|--------|-------|-----------------|---------|------------------------------|
| `security-policy` | Secure development | `<name>` | `<link>` | `<x.y>` | `block-secrets.sh` hook, review Security pass |
| `secure-api-review` | API security standard | `<name>` | `<link>` | `<x.y>` | `check-endpoints.sh`, review Security pass |
| `compliance-policy` | `<GDPR / SOC 2 / ...>` | `<name>` | `<link>` | `<x.y>` | review Conformance pass |
| `brand-guidelines` | Brand & content | `<name>` | `<link>` | `<x.y>` | review Conformance pass |
| `ux-standards` | UX & accessibility | `<name>` | `<link>` | `<x.y>` | screenshot check, `<a11y CI check>` |
| `intent-template` | Intent format | `<name>` | `intent/0000-template/intent.md` | `<x.y>` | CODEOWNERS on `intent/` |

A skill is an advisory control. A policy that must hold without exception needs a
deterministic control behind it (last column): a hook, a CI check or a review pass.

**Measure:** time from policy approval to the updated skill merging; PR findings citing each policy (should trend to zero).
