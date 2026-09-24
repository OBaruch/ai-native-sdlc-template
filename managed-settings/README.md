# managed-settings/

Organization-wide Claude Code policy for regulated environments. This folder is only the
**reviewed source**: the file takes effect when the platform/IT team deploys it through MDM or
the Claude admin console (server-managed settings). Engineers cannot override managed settings.

Start from `managed-settings.json`, replace every `<placeholder>`, and remove what does not fit
the data classification of your repositories. Every deny rule removes capability, so tune it.

## What each block controls

| Key | Control objective |
|-----|-------------------|
| `permissions.deny` | Secrets never enter the agent's context; no arbitrary network egress through tools |
| `permissions.allow` | Pre-approve the safe inner loop (build/test/lint/git read) so the deny list does not cause prompt fatigue |
| `disableBypassPermissionsMode` + `allowManagedPermissionRulesOnly` | Nobody (user, project file, CLI flag) can widen the rules |
| `sandbox` | OS-level isolation. Blocks egress to anything outside `allowedDomains` even from shell commands; `failIfUnavailable` / `allowUnsandboxedCommands: false` make the sandbox a precondition |
| `sandbox.credentials` | Sandboxed shell commands cannot read credential files or inherit the listed secret env vars |
| `allowManagedHooksOnly` | Only hooks defined here run. **Project hooks in `.claude/settings.json` stop running**, so every gate you need (e.g. the production gate) must be declared in this file's `hooks` block |
| `allowManagedMcpServersOnly` | The agent's tool surface is an allowlist owned by the platform team |
| `disableSideloadFlags` + `strictKnownMarketplaces` | Skills, agents, hooks and MCP servers only come from the approved plugin marketplace |
| `env` (OTEL_*) | Sessions, tool decisions and hook verdicts are exported to your observability stack; most leading indicators in `governance/metrics.md` come from here |
| `requiredMinimumVersion` | Refuses to start below the version your security team assessed |

## Change process
Changes to this folder need approval from `@your-org/platform-team` and `@your-org/security`
(`.github/CODEOWNERS`), and should run the agent evals (`evals/`) before rollout.

Reference: the Claude Code settings documentation lists every key, including the managed-only ones.
