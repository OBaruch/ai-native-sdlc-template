# Portable agent contract

`AGENTS.md` is the instruction entry point. `.agents/skills`, `commands`, `roles` and
`hooks` are the source of truth. Harness discovery files are adapters, not policy sources. Roles declare neutral read/search/write/shell capabilities; task procedures use {{arguments}}. Generated adapters translate these into native metadata and parameters.
See [adoption](../docs/adoption.md) and [migration](../docs/migration.md).

## Execution

Choose `SDLC_AGENT_ADAPTER=claude`, `codex`, or `command`; no provider is selected implicitly.
The common entry point is `scripts/agent_run.py`. It reads a prompt file, prepends AGENTS.md,
runs in the requested workspace, enforces a wall-clock timeout on the process group and
writes a normalized result. Empty/malformed responses and nonzero CLI exits fail the task.
The runner does not approve, commit, push, merge, deploy or publish by itself.
Native runs explicitly disable inherited MCP servers so a permission mode cannot silently
expose remote write/deployment tools. Add required connectors through a separately reviewed
adapter/orchestrator with scoped identity and explicit policy checks.

| Adapter | Integration | Read-only boundary | Workspace-write boundary |
|---------|-------------|--------------------|--------------------------|
| Claude Code | Native CLI flags + generated instruction/skill/role/hook discovery | Only Read/Grep/Glob tools exposed | Edit/Write and scoped Make/Git tools; shared policy hooks |
| Codex | Native `exec`, AGENTS.md, final-message capture | Native `--sandbox read-only` | Native `--sandbox workspace-write`; common policy is **not automatically a Codex hook** |
| Any other CLI/SDK, including Hermes, Muse, Dots or Grok | JSON command adapter written by the adopter | Adapter must implement it and use an external sandbox | Adapter must implement scoped writes and map approvals |

Native adapters are tested offline with executable fixtures. Live model behavior requires a
pinned CLI, working credentials and enabled project-specific evals. Vendor versions and
third-party harnesses must be validated in the adopter's environment; this template does
not claim native integrations for undocumented CLI flags. CLI flags were checked against
Claude Code 2.1.300 and Codex CLI 0.159.2; choose a tested version when adopting or upgrading.

### Command adapter

`SDLC_AGENT_COMMAND` is a JSON argument array, never a shell expression. For example:
`["python3", "scripts/my_harness_adapter.py"]`. The executable receives exactly one request
JSON on stdin and must return one result JSON on stdout. Diagnostic logs go to stderr.
Configure `SDLC_AGENT_MODES` as a comma-separated list of modes the adapter actually enforces.
Missing mode support fails before execution. These declarations are **not a sandbox**.

Request (`contracts/request.schema.json`):

```json
{
  "schema_version": 1,
  "prompt": "canonical instructions followed by the task",
  "workspace": "/absolute/project/path",
  "mode": "read-only",
  "timeout_seconds": 600,
  "instructions": {
    "entrypoint": "AGENTS.md",
    "skills": ".agents/skills",
    "commands": ".agents/commands",
    "roles": ".agents/roles"
  }
}
```

Result (`contracts/result.schema.json`):

```json
{"schema_version": 1, "status": "success", "is_error": false, "output": "Markdown answer"}
```

Failures use `status: error`, `is_error: true` and a nonzero process exit. The runner adds the
selected `adapter` to its stored result. `is_error` remains portable for existing eval field checks.
Never return provider credentials or raw session transcripts. Result/output paths are host
artifacts; the agent's permission mode governs model tools, not the orchestrator writing results.

## Policy events

A harness with pre/post-tool hooks can translate each native action into this event and call
`python3 scripts/policy.py --project /absolute/project/path` with JSON on stdin:

```json
{"schema_version": 1, "phase": "before", "operation": {"kind": "write", "path": "src/app.py", "content": "proposed content"}}
```

Event/decision schemas live in `contracts/event.schema.json` and `contracts/decision.schema.json`.

Phases: `before`, `after`, `finish`. Before/after operations: `read` (path), `write` (path and
proposed content/new_string/edits/new_source), `shell` (command). Finish uses `kind: none`.
Translate multi-file edits into separate events for **every** affected file before execution.
Paths are normalized and may not escape the project, including through symlinks.

Response: `{"decision": "allow|deny|ask", "reason": "..."}`. Exit 0 means allow; exit 2 means
blocked or human approval needed. Invalid events, invalid hook results and hook crashes deny.
An adapter must suspend an `ask` action until a human authorizes it; treating `ask` as allow
is a contract violation. An agent cannot grant itself approval through its request.

Shell matching is a heuristic, not a shell parser or an OS security boundary. File hooks do
not inspect every possible shell side effect. Use a real sandbox, scoped identities,
branch protection/CODEOWNERS and protected deployment environments for authoritative gates.
A harness without pre-tool hooks still uses the same instructions and CI, but does **not**
gain proactive per-tool enforcement merely by reading AGENTS.md.

## State and compatibility

Session markers: `.agents/active-change`, `.agents/fix-task`; audit output: `.agents/logs`.
`python3 scripts/verify.py` records successful application checks against a hash of HEAD and
tracked/untracked, nonignored working-tree contents; `--template` verifies this scaffold.
Later content changes invalidate the receipt. Receipts are local evidence, not signed or
immutable attestations: the trusted CI and review gates remain authoritative.

`make sync-adapters` regenerates CLAUDE.md, Claude skills/commands/agents and thin hook bridges.
`make adapter-check` rejects drift, including stale extra generated files; migration never
silently deletes user files. Existing `.claude/active-change` and `.claude/fix-task` markers
are recognized at the Claude boundary during migration. Claude's Stop recursion guard is
kept for compatibility; it does not replace required CI checks.
