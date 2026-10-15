# Portable agent runtime

Build from the repository root:

```bash
docker build -f sandbox/Dockerfile -t ai-native-sdlc .
docker run --rm --read-only --network none ai-native-sdlc --help
```

The default image installs shared tools, runs as an unprivileged user and has no harness or
credentials baked in. Bind the project to `/workspace` for agent tasks. Mount an appropriate
writable result directory explicitly; read-only tasks should mount the project read-only.
The runner's permission mode does not itself configure Docker mount, egress or identity policy.

Native CLI installation is optional and requires an exact version:

```bash
docker build -f sandbox/Dockerfile --build-arg SDLC_AGENT_ADAPTER=codex \
  --build-arg SDLC_AGENT_VERSION=YOUR_TESTED_VERSION -t ai-native-sdlc-codex .
```

Use an allowlisting egress proxy or FQDN-aware CNI for the selected model/package/MCP
destinations. `network-policy.yaml` is a Kubernetes example with organizational placeholders,
not a complete local Docker sandbox. Keep production identities outside ordinary agent jobs.

For an enterprise proxy, BuildKit supports predefined HTTP_PROXY/HTTPS_PROXY/NO_PROXY build
arguments. If its public CA certificate is required, mount the approved **CA bundle only**
(no private key) with `--secret id=build_ca,src=/path/to/approved-ca-bundle.pem`. The build
temporarily uses that trust bundle for HTTPS Debian/npm requests, preserving certificate and
signed-package verification; the bundle and temporary apt configuration are not saved in the
image. Configure the supported DNS/proxy route for your container engine. Never disable TLS
or package-signature verification to make a build pass. Runtime trust/credentials must be
provided separately through your platform's supported settings.
