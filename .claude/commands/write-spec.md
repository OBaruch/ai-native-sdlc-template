---
description: Produce spec.md (requirements + design) from an accepted intent.md, constrained by the organization's skills
argument-hint: <path to intent folder, e.g. intent/0007-claims-status>
---

Change folder: `$ARGUMENTS`

1. Read `$ARGUMENTS/intent.md`. If it is missing or its status is not `accepted`, stop and say so.
2. Load every policy skill that applies (security-policy, compliance-policy, brand-guidelines,
   ux-standards, secure-api-review and any organization skill that matches the change).
3. Study the parts of this codebase the intent touches so the spec fits what already exists.
4. Write `$ARGUMENTS/spec.md` following the structure of `intent/0000-template/spec.md`:
   - requirements traceable to the intent's problem and outcome;
   - a design that integrates with the existing code;
   - a section per applicable policy saying how the design satisfies it;
   - every open question from the intent either answered or carried forward.
5. **Areas of concern** is the most important section. List every point where a policy cannot be
   met, two policies contradict each other, or the intent is ambiguous. Name the policy owner
   who must decide. Do not resolve conflicts yourself.
6. Record the skill names and versions you applied in the spec's frontmatter.

Do not write code and do not create `plan.md`. Finish with a short summary of the concerns
the product owner must resolve before engineering starts.
