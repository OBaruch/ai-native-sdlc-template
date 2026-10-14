# Adopt the template — humans and agents

[Español](adoption.es.md) · [Contract](../.agents/README.md) · [Migration](migration.md)

## Template, fork, or clone?

| Goal | Recommended method | Consequence |
|------|--------------------|-------------|
| Start your own application or internal SDLC repo | **Use this template → Create a new repository** | Independent repository and history; your permissions, secrets and CI settings |
| Contribute improvements to this template, or maintain an upstream relationship | **Fork** | GitHub preserves the upstream relation; use PRs and sync-fork to exchange changes |
| Inspect locally or work on an existing repository | **Clone** | A local checkout; cloning alone does not create a new GitHub project |

On GitHub open `OBaruch/ai-native-sdlc-template` and choose **Use this template**. If the button
is unavailable, the owner must enable **Settings → General → Template repository**; a fork
is a usable fallback. From the CLI, when the template setting is enabled:

```bash
gh repo create YOUR_OWNER/YOUR_PROJECT --template OBaruch/ai-native-sdlc-template --private --clone
cd YOUR_PROJECT
```

Choose public/private according to your organization. Template creation does not copy upstream
secrets, repository variables, branch protections, environments, or external integrations.
A fork also needs its own settings; do not assume credentials or approval gates were inherited.
Use branches and reviewable PRs in your new repo. Do not push your application's changes here.

For an existing repository, copy the desired scaffold into a branch, preserving its code,
Git history, instruction files and CI. Resolve conflicts explicitly; do not overwrite an
existing AGENTS.md or `.claude` directory. A source archive can be used when GitHub template
creation is unavailable and you want independent history; initialize a new repository only
after reviewing the copied files and excluding credentials/local artifacts.

## First local checks (no model account needed)

Prerequisites: Python 3.12, Bash, Git, Make and ShellCheck. jq is optional (Python fallback).
Install ShellCheck using your OS package manager, for example `apt-get install shellcheck`
or `brew install shellcheck`. Use an isolated Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install 'PyYAML==6.0.3'
make doctor
make template-check
```

On Windows use WSL or Git Bash with the same tools. Cloud tasks are already isolated; keep
the existing checkout and do not create worktrees unless the user explicitly requests them.
`template-check` validates the scaffold without calling a model. Application Make targets
still fail until you set BUILD_CMD, TEST_CMD, LINT_CMD, ITEST_CMD and RUN_CMD for your stack.

## Let your agent adopt it

Give any agent this task (or link this document when it discovers the repository):

> Read AGENTS.md, .agents/README.md and docs/adoption.md. Inspect the existing project before
> editing. Keep one authoritative set of instructions in AGENTS.md and .agents. Propose and
> implement the project-specific setup in a branch without overwriting existing instructions,
> secrets, application code or CI. Reuse existing authentication and inspect only credential
> names/presence. Choose a harness adapter explicitly; verify its actual permission boundaries.
> Configure the application Make commands, policy owners, first intent and human review gates.
> Run doctor, template-check and the application's checks. Report passed, failed, disabled and
> unrun checks separately. Open a PR for human approval; never approve, merge or deploy yourself.

Codex discovers AGENTS.md; Claude Code uses the generated CLAUDE.md import and discovery files.
For harnesses that do not discover AGENTS.md automatically, configure their instruction entry
point or pass its contents explicitly. Skills and roles are ordinary Markdown: load applicable
files even when the harness has no native skill/subagent registry. A slash command is optional;
the same task can be requested using `.agents/commands/<task>.md` as a procedure.

## Select a harness

```bash
export SDLC_AGENT_ADAPTER=codex  # or claude
export SDLC_AGENT_VERSION=YOUR_EXACT_CLI_VERSION
python3 scripts/install_agent.py
make doctor
mkdir -p out
printf '%s\n' 'Inspect this repository and suggest the first adoption steps; do not edit files.' > out/task.md
python3 scripts/agent_run.py --prompt-file out/task.md --mode read-only --output out/result.json --text
```

Use an exact version such as the version your team has validated, not `latest`. Configure
credentials using the harness's existing login or secure environment settings. Codex can use
OPENAI_API_KEY; Claude can use ANTHROPIC_API_KEY. Never paste key values into prompts, committed
files or chat. Local authentication does not establish CI authentication.

For Hermes, Muse, Dots, Grok or another CLI/SDK, implement the [JSON command contract](../.agents/README.md):

```bash
export SDLC_AGENT_ADAPTER=command
export SDLC_AGENT_COMMAND='["python3", "scripts/my_harness_adapter.py"]'
export SDLC_AGENT_MODES=read-only  # declare only modes actually enforced by your adapter/sandbox
make doctor
```

The named adapter script must exist and be implemented by you; it is an example path, not a
bundled vendor integration. It translates provider input/output, installs any project-approved
dependencies, rejects unsupported modes and maps policy decisions if native hooks exist.
Run an offline contract test and a representative live task before enabling automation.

If your CLI accepts a text prompt on stdin and returns its final answer on stdout, use the
bundled shim instead of writing code:

```bash
export SDLC_AGENT_ADAPTER=command
export SDLC_AGENT_COMMAND='["python3", ".agents/adapters/stdin_cli.py"]'
export SDLC_AGENT_MODES=read-only
export SDLC_HARNESS_MODE_COMMANDS='{"read-only":["YOUR_CLI","YOUR_VERIFIED_READ_ONLY_FLAGS","-"]}'
```

Replace that example argument array with the actual documented invocation and enforced
sandbox for your CLI. Configure each mode separately; absent modes fail. No flags or vendor
APIs are guessed. SDK integrations or CLIs with different input/output formats need a custom
protocol adapter. Models/providers are selected by your harness configuration, not hardcoded
by the SDLC core. In GitHub Actions also expose SDLC_HARNESS_MODE_COMMANDS to the runner.

## Activate shared automation

1. Replace the project/policy/team placeholders in AGENTS.md, skills, REVIEW.md, governance and CODEOWNERS.
2. Set the application Make commands and implement deployment/rollback for your platform.
3. Configure GitHub variables SDLC_AGENT_ADAPTER, SDLC_AGENT_VERSION (native CLI), or SDLC_AGENT_COMMAND
   and SDLC_AGENT_MODES (command adapter). Hosted runners need the custom executable/dependencies
   available; vendor-specific setup belongs in your reviewed setup action, not the portable runner.
4. Add only the selected provider credential, or SDLC_AGENT_TOKEN for your command adapter, securely.
   Configure required provider/package/MCP destinations in your runtime's network policy.
5. Replace and enable real evals; `bash evals/run.sh --require-enabled` must run actual cases.
   Schedule or manually dispatch credentialed evals on a maintainer-approved ref. PR contract tests
   use no secrets; PR-supplied eval commands are never automatically executed with provider secrets.
6. Enable SDLC_ENABLED=true after those checks, branch protection/CODEOWNERS and the dev/staging/production
   environments (production requires named reviewers). Generic agent review, CI triage, spec drafting,
   monitoring and evals all use the common runner. Legacy @claude action workflows additionally require
   SDLC_CLAUDE_ACTION_ENABLED=true and the claude adapter; they are optional and off by default.

The template's organizational policy values are placeholders; copying it does not configure your
actual GitHub protections or production permissions. Confirm gates with your team before deployment.
For upstream updates to an independent template-derived repo, review the upstream diff and port
selected scaffold changes into a PR; there is no automatic sync-fork history relationship.
