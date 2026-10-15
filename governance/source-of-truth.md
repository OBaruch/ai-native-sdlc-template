# Source of truth per artifact

<!-- TEMPLATE: for each artifact, name ONE authoritative system. The others hold a copy or a link.
The AI-native Markdown chain can coexist with Jira / ServiceNow / a requirements tool as long
as this table is explicit. -->

Configuration options:
- **Repo is the truth** — Markdown in `intent/` is authoritative; the legacy record links to the commit.
- **Legacy is the truth** — the legacy record is authoritative; the agent reads it at session start and writes the outcome back through an MCP connector; Markdown files are working copies.
- **Linkage (minimum bar)** — both exist; every Markdown artifact carries `record_id`, every legacy record carries the commit SHA.

| Artifact | Source of truth | Copy / link in | How they are linked |
|----------|-----------------|----------------|---------------------|
| Idea / intent | `<repo intent/ | Jira>` | `<...>` | `record_id` in frontmatter ↔ commit SHA in the record |
| Requirements (spec) | `<repo | requirements tool>` | `<...>` | `<...>` |
| Design mocks | `<Figma / the agent Design>` | linked from `spec.md` | URL in spec |
| Implementation plan | repo `plan.md` | linked from the ticket | commit SHA |
| Change approval | `<ServiceNow change / PR approval>` | `<...>` | ticket id in `RELEASE_APPROVAL` / `CHANGE_TICKET` |
| Incident | `<incident tool>` | `postmortems/` | incident id in file name |
