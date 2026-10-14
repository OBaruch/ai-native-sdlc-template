---
id: 0001-harness-agnostic
spec: ./spec.md
status: implemented
approved_by: Implementation requested in chat; manual PR approval pending
date: 2026-10-14
---

# Plan: Harness-independent SDLC

## Files that change
- AGENTS.md and .agents/ (new): canonical instructions, skills, procedures, roles, CLI shim and policy hooks/contracts.
- scripts/agent_run.py, policy.py, claude_hook.py, verify.py, run_evals.py, install_agent.py,
  sync_adapters.py, doctor.py, write_specs.py, respond.py (new): portable runtime and orchestration.
- CLAUDE.md and .claude/ (modified): generated compatibility files; native settings retained.
- Makefile, scripts/validate_template.py, evals/, monitoring/ and .github/ (modified): shared checks/workflows.
- tests/test_runtime.py, tests/test_automation.py and tests/test_discovery.py (new): offline behavioral/contract coverage.
- README.md, docs/, llms.txt, governance/, REVIEW.md, intent templates and lesson map (new/modified): adoption and ownership.
- sandbox/, .dockerignore, .gitignore (modified/new): optional versioned harness installation and local artifacts.

## Order of work
1. Preserve the baseline tests and create a separate branch.
2. Introduce the portable instruction/event/request/result contracts and native adapter boundary.
3. Replace direct model calls; isolate eval runs and keep publication in trusted orchestrators.
4. Document adoption/migration and configure vendor-independent owners/gates.
5. Add offline failure/isolation/permission tests, run scaffold checks and review the complete diff.
6. Commit, push and open a PR for manual approval; do not merge.

## Risks
CLI APIs and authentication vary; offline fixtures validate translation, not live model behavior.
Prompt instructions and local receipts are not immutable enforcement. The command adapter requires
an actual sandbox. Custom installations must migrate content before regenerating vendor copies.

## Proof
- Existing hook and detector suites remain green.
- Protocol tests cover native CLI translation, missing modes, malformed results, timeouts and clone isolation.
- Policy tests deny unsupported events, secret access and generated-path traversal.
- Validator/drift/ShellCheck and workflow validation pass; zero enabled model evals remain explicitly skipped.
- Sandbox image behavior is checked if a working container daemon/network is available.

## Rollback
Revert the implementation commit; the baseline Claude configuration remains available in Git history.
