---
description: Draft plan.md for an approved spec (use in plan mode), then iterate with the engineer
argument: <path to intent folder, e.g. intent/0007-claims-status>
---

Change folder: `{{arguments}}`

You are in the planning step. Do not modify source code.

1. Read `{{arguments}}/intent.md` and `{{arguments}}/spec.md`. If the spec is not `approved`, stop and say so.
2. Read `AGENTS.md` and explore the code the spec touches.
3. Propose an implementation plan using the structure of `intent/0000-template/plan.md`:
   - exact files that change (new / modified / deleted);
   - order of work as small, independently verifiable steps;
   - risks: what could break, the riskiest step, and the alternatives you rejected and why;
   - proof: the tests and checks that will show it works, stated as pass/fail targets;
   - which steps are independent. Cloud tasks are already isolated; create worktrees only when explicitly requested.
4. Invite the engineer to interrogate it. Revise until someone who never saw this
   conversation could implement the change from the plan alone.
5. When the engineer approves, write it to `{{arguments}}/plan.md` with `status: approved`, the
   approver and the date, and run `echo {{arguments}} > .agents/active-change`.
