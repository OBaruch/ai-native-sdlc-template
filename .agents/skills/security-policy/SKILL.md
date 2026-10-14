---
name: security-policy
description: Apply the organization's secure development policy. Use when writing a spec or plan, handling authentication, secrets, cryptography, file uploads, external input, third-party dependencies, or any data classified as confidential or personal.
---

# Secure development policy

Owner: `<CISO delegate>` · Source of truth: `<link to the security policy>` · Policy version: `<x.y>`

<!-- TEMPLATE: replace each rule with your organization's policy text, keeping one rule per line. -->

## Rules
1. **Secrets**: never in code, config files or logs. Read them from `<secret manager>`.
2. **Dependencies**: only from `<approved registries>`; no new dependency without a licence and
   vulnerability check (`<tool>`); never bump versions the platform team owns.
3. **Cryptography**: use `<approved library>`; no custom crypto; minimum `<TLS 1.2 / AES-256 / ...>`.
4. **Data classification**: `<public | internal | confidential | restricted>`. Restricted data
   stays in `<approved stores>` and is encrypted at rest.
5. **External input**: validate at the boundary; parameterized queries only; no shell
   interpolation of user input.
6. **Logging**: log security events (auth failures, permission denials) without personal data.
7. **Threat model**: changes that add a new trust boundary need a short threat model in `spec.md`.

## When writing a spec or plan
List each rule the change touches and how it is satisfied. Where two rules or two policies
conflict, do not choose: record it under **Areas of concern** and name this policy's owner.
