# Sandbox image for non-interactive agent jobs (CI triage, evals, maintain loop).
# No credentials are baked in: inject short-lived, scoped tokens at runtime and run the
# container under sandbox/network-policy.yaml (egress allowlist).
FROM node:22-slim

ARG CLAUDE_CODE_VERSION=latest

RUN apt-get update \
 && apt-get install -y --no-install-recommends git make jq python3 python3-yaml ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# GitHub CLI (used by the maintain loop and PR tooling)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
 && apt-get update && apt-get install -y --no-install-recommends gh \
 && rm -rf /var/lib/apt/lists/*

RUN npm install -g "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}"

# Unprivileged user, read-only home by convention, workspace mounted at runtime.
RUN useradd --create-home --shell /bin/bash agent
USER agent
WORKDIR /workspace

ENV CLAUDE_CODE_ENABLE_TELEMETRY=1

ENTRYPOINT ["claude"]
CMD ["--help"]
