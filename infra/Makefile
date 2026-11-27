# Shortcuts for the Docker stack: the agent API and the web app, each its own
# compose project on the `voiceagent-net` network (created by the backend file).
.DEFAULT_GOAL := help
.PHONY: help stack-up stack-down

BACKEND := docker compose -f docker-compose.backend.yml
FRONTEND := docker compose -f docker-compose.frontend.yml

help: ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

stack-up: ## Start the agent API, then the web app, in Docker
	$(BACKEND) up -d --build --wait
	$(FRONTEND) up -d --build --wait

stack-down: ## Stop the web app and the agent API
	$(FRONTEND) down
	$(BACKEND) down
