# Shared runtime. No harness or credentials are installed by default.
# Build from repo root: docker build -f sandbox/Dockerfile .
FROM node:22-slim
ARG SDLC_AGENT_ADAPTER=none
ARG SDLC_AGENT_VERSION
RUN --mount=type=secret,id=build_ca,mode=0444 \
    if [ -s /run/secrets/build_ca ]; then \
      sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources; \
      printf '%s\n' 'Acquire::https::CaInfo "/run/secrets/build_ca";' > /etc/apt/apt.conf.d/99-build-ca; \
    fi \
 && apt-get -o APT::Update::Error-Mode=any update \
 && apt-get install -y --no-install-recommends git make jq python3 python3-yaml shellcheck ca-certificates curl \
 && rm -rf /var/lib/apt/lists/* \
 && rm -f /etc/apt/apt.conf.d/99-build-ca
COPY scripts /opt/sdlc/scripts
COPY .agents /opt/sdlc/.agents
RUN --mount=type=secret,id=build_ca,mode=0444 \
    if [ -s /run/secrets/build_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/build_ca; fi; \
    if [ "$SDLC_AGENT_ADAPTER" != none ]; then \
      SDLC_AGENT_ADAPTER="$SDLC_AGENT_ADAPTER" SDLC_AGENT_VERSION="$SDLC_AGENT_VERSION" python3 /opt/sdlc/scripts/install_agent.py; \
    fi
RUN chmod -R a+rX /opt/sdlc \
 && useradd --create-home --shell /bin/bash agent
USER agent
WORKDIR /workspace
ENTRYPOINT ["python3", "/opt/sdlc/scripts/agent_run.py"]
CMD ["--help"]
