---
description: Brainstorm an idea with the originator and capture it as intent/NNNN-slug/intent.md
argument-hint: <one-line description of the idea or ticket id>
---

Starting point: $ARGUMENTS

Use the `intent-template` skill. Interview me one question at a time until every section of
`intent/0000-template/intent.md` can be filled in my own words. Then:

1. Pick the next free number in `intent/` and a short kebab-case slug.
2. Create `intent/NNNN-slug/intent.md` from the template with `status: draft`.
3. Show me the draft and apply my corrections.
4. When I confirm, create a branch `intent/NNNN-slug`, commit the file and open a PR for the
   product owner (`gh pr create`), or tell me the commands if you cannot.
