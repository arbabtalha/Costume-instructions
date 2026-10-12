# Costume Webapp Kit

SHELL := /bin/bash
.DEFAULT_GOAL := help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Install the kit into this repo's own project layout (client: all)
	./scripts/setup.sh --target . --client all

site: ## Rebuild the documentation site and public repository search index
	python3 scripts/build-site.py --out index.html

verify: ## Run the full check suite
	./scripts/verify.sh

test: verify site ## Verify, then rebuild the site and confirm it is current
	@python3 scripts/build-site.py --check
	@git diff --quiet -- index.html repository-files.json || echo "note: generated site files changed - commit them"

vendor-update: ## Refresh vendored skills from upstream repos
	./scripts/vendor-update.sh

vendor-check: ## Report upstream versions vs vendored
	./scripts/vendor-update.sh --check

mcp: ## Install the MCP config only (client: all)
	./scripts/install-mcp.sh --client all

clean: ## Remove local build/test leftovers (never touches tracked files)
	@find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete 2>/dev/null || true
	@rm -rf .costume-backup design-system

.PHONY: help setup site verify test vendor-update vendor-check mcp clean
