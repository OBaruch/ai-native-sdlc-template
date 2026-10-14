---
name: secure-api-review
description: Apply the API security standard. Use whenever you create or change an HTTP/gRPC endpoint, route, controller or handler, review API code, or write or modify an OpenAPI/proto contract.
---

# Secure API standard

Owner: `<security architect>` · Source of truth: `<link to the API security policy>` · Policy version: `<x.y>`

Apply every rule below to each endpoint you add or change.

1. **Authentication**: every route requires `<the gateway token / session mechanism>`.
   The only anonymous routes are `<e.g. /health, /ready>`.
2. **Authorization**: check the caller's permission for the specific resource, not only
   that they are logged in. Deny by default.
3. **Input validation**: validate path, query and body against the contract
   (`<OpenAPI/proto location>`); reject unknown fields; bound sizes and lengths.
4. **Output**: return only fields the contract declares. Errors never echo input, stack
   traces or internal identifiers.
5. **Audit**: every state-changing call emits an audit event with actor, action, target and
   time via `<audit library/function>`.
6. **Sensitive data**: fields classified as `<pii / confidential>` never appear in logs,
   metrics labels or error messages.
7. **Rate limiting**: public endpoints declare a limit in `<where limits are configured>`.

## Check
Run `bash .agents/skills/secure-api-review/scripts/check-endpoints.sh` and include its
output in your summary. If it reports a finding you believe is wrong, say so explicitly
instead of silencing it.

## If a rule cannot be met
Stop and flag it as an area of concern for the policy owner. Do not invent an exception.
