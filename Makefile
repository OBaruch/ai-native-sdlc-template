# Single-command verification targets (feedback loop).
# Set each *_CMD for your stack. Every target must exit non-zero on failure.
# Until a command is set, its target fails loudly instead of pretending to pass.

BUILD_CMD ?=
TEST_CMD  ?=
ITEST_CMD ?=
LINT_CMD  ?=
RUN_CMD   ?=
PYTHON    ?= python3

.PHONY: help build test itest lint run check validate-template hook-test monitor-test evals agent-test sync-adapters adapter-check template-check shellcheck doctor

help:
	@echo "build | test | itest | lint | run   project targets (configure *_CMD in Makefile)"
	@echo "check                               lint + test + build (what 'done' means)"
	@echo "validate-template                   validate the SDLC scaffold itself"
	@echo "hook-test                           Claude compatibility regression tests"
	@echo "monitor-test                        unit tests for monitoring/detect.py"
	@echo "evals                               run evals using SDLC_AGENT_ADAPTER"
	@echo "agent-test | adapter-check           portable runtime tests and adapter drift check"
	@echo "template-check                      all scaffold checks (no model credentials needed)"
	@echo "sync-adapters | doctor              regenerate discovery files; diagnose prerequisites"

build:
ifeq ($(strip $(BUILD_CMD)),)
	@echo "make build: not configured. Set BUILD_CMD in the Makefile (see AGENTS.md > Commands)." >&2; exit 1
else
	$(BUILD_CMD)
endif

test:
ifeq ($(strip $(TEST_CMD)),)
	@echo "make test: not configured. Set TEST_CMD in the Makefile (see AGENTS.md > Commands)." >&2; exit 1
else
	$(TEST_CMD)
endif

itest:
ifeq ($(strip $(ITEST_CMD)),)
	@echo "make itest: not configured. Set ITEST_CMD in the Makefile (see AGENTS.md > Commands)." >&2; exit 1
else
	$(ITEST_CMD)
endif

lint:
ifeq ($(strip $(LINT_CMD)),)
	@echo "make lint: not configured. Set LINT_CMD in the Makefile (see AGENTS.md > Commands)." >&2; exit 1
else
	$(LINT_CMD)
endif

run:
ifeq ($(strip $(RUN_CMD)),)
	@echo "make run: not configured. Set RUN_CMD in the Makefile (see AGENTS.md > Commands)." >&2; exit 1
else
	$(RUN_CMD)
endif

check: lint test build

validate-template:
	$(PYTHON) scripts/validate_template.py

hook-test:
	bash scripts/test_hooks.sh

monitor-test:
	$(PYTHON) -m unittest discover -s monitoring/tests -v

evals:
	bash evals/run.sh

agent-test:
	$(PYTHON) -m unittest discover -s tests -v

sync-adapters:
	$(PYTHON) scripts/sync_adapters.py

adapter-check:
	$(PYTHON) scripts/sync_adapters.py --check

shellcheck:
	@command -v shellcheck >/dev/null || { echo "Install ShellCheck before template-check." >&2; exit 1; }
	@find .agents .claude scripts evals monitoring -name '*.sh' -print0 | xargs -0 -r shellcheck -S error -x

template-check: validate-template adapter-check hook-test agent-test monitor-test shellcheck

doctor:
	$(PYTHON) scripts/doctor.py
