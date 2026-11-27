# Shortcuts for the voice agent; run from this directory (`make` lists them).
# The gates are the CI ones (scripts/ci/python-checks.sh), run from the repo root.
.DEFAULT_GOAL := help
.PHONY: help install env dev fmt test audit coverage openapi shell \
        docker-up docker-down docker-logs docker-ps clean

ROOT := ../..
GATE := cd $(ROOT) && scripts/ci/python-checks.sh agents/voice_agent
COMPOSE := docker compose -f $(ROOT)/infra/docker-compose.backend.yml
SERVICE := voice-agent-api

help: ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install: ## Sync the virtualenv (with dev tools) from uv.lock
	uv sync --locked

env: ## Create .env from .env.example (never overwrites an existing .env)
	@test -f .env && echo ".env already exists, leaving it alone" \
		|| (cp .env.example .env && echo "Created .env: fill in the API keys")

dev: ## Run the API with reload on :8000
	./run.sh api

fmt: ## Format the code and apply safe lint fixes
	uv run ruff format .
	uv run ruff check --fix .

test: ## Lint, format check, Pyright strict, tests and coverage floor (CI unit gate)
	$(GATE) unit

audit: ## Dependency audit (pip-audit on the locked runtime dependencies)
	$(GATE) audit

coverage: ## Tests with a line-by-line coverage report
	uv run pytest tests --cov --cov-report=term-missing

openapi: ## Re-export the OpenAPI document and regenerate the web contract types
	uv run python -m voice_agent.export_openapi > $(ROOT)/libs/voice-agent-contracts/openapi.json
	cd $(ROOT) && pnpm --filter @voiceagent/voice-agent-contracts generate

shell: ## Python REPL with the project environment
	uv run python

docker-up: ## Build and start the agent in Docker
	$(COMPOSE) up -d --build --wait $(SERVICE)

docker-down: ## Stop and remove the agent's container only
	$(COMPOSE) rm -sf $(SERVICE)

docker-logs: ## Follow the agent's Docker logs
	$(COMPOSE) logs -f $(SERVICE)

docker-ps: ## Show the agent's container
	$(COMPOSE) ps -a $(SERVICE)

clean: ## Remove bytecode here and the shared tool caches at the repo root
	find . -type d -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} +
	rm -rf $(ROOT)/.pytest_cache $(ROOT)/.ruff_cache $(ROOT)/.coverage
