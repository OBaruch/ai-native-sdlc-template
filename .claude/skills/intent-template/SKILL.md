---
name: intent-template
description: Turn an idea, ticket or incident into this organization's intent.md format. Use when someone describes a problem or feature they want, asks to "write an intent", "capture this idea", or when a monitoring finding must be written up for triage.
---

# Writing an intent.md

Owner: `<product operations lead>` · Source of truth: `intent/0000-template/intent.md`

An intent is a short proto-spec written in the originator's own words. It says what is
wanted, why, and under which constraints. It does **not** design the solution.

## Before writing
Interview the originator until you can fill every section. Ask one question at a time, the
way an analyst would:
- Who is affected today, and what can't they do?
- What does "better" look like, and how would we notice it?
- What is explicitly out of scope?
- Which systems, data and teams are touched?
- Which constraints are fixed (regulation, budget, dates, existing auth, data classes)?

Stop asking when the answers stop changing the document.

## Writing it
1. Copy the structure of `intent/0000-template/intent.md` exactly; keep the frontmatter keys.
2. Create the folder `intent/NNNN-short-slug/` using the next free number.
3. Keep the originator's vocabulary. Do not add solutions, estimates or technology choices.
4. Put anything uncertain under **Open questions**, never as an assumption in another section.
5. Set `source:` to `idea`, `ticket` (with `record_id`) or `incident` (with the alert/incident id).
6. Show the draft to the originator and apply their corrections before anything is committed.

## Done when
- Every section is filled or explicitly marked `none`.
- The originator confirmed the draft.
- It is committed (or opened as a PR) so the product owner can accept or close it.
