.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  uv-sync   Restore the local environment exactly from uv.lock"
	@echo "  stage-web Generate the ignored Pyodide package bundle and manifest"
	@echo "  fmt       Format code (ruff)"
	@echo "  lint      Lint code (ruff)"
	@echo "  golden-check Verify frozen numerical and browser-contract fixtures"
	@echo "  portfolio-links Validate catalog/focused/Core navigation"
	@echo "  test      Run non-E2E tests (pytest)"
	@echo "  e2e       Run Playwright browser tests"
	@echo "  serve     Serve the web app locally"
	@echo "  verify    Run format check, lint, non-E2E tests, and E2E tests"
	@echo "  clean     Remove caches / local build artifacts"

.PHONY: uv-sync
uv-sync:
	uv sync --locked

.PHONY: stage-web
stage-web:
	uv run python scripts/stage_web_python.py

.PHONY: fmt
fmt:
	uv run ruff format .

.PHONY: fmt-check
fmt-check:
	uv run ruff format --check .

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: golden-check
golden-check:
	uv run python scripts/generate_golden_baseline.py --check
	uv run python scripts/compare_golden_baseline.py

.PHONY: portfolio-links
portfolio-links:
	uv run python scripts/check_portfolio_links.py

.PHONY: test
test: stage-web golden-check
	uv run pytest -q -m "not e2e"

.PHONY: e2e
e2e: stage-web
	uv run pytest -q -m e2e \
		--browser chromium \
		--tracing retain-on-failure \
		--video retain-on-failure \
		--screenshot only-on-failure \
		--output test-results

.PHONY: serve
serve: stage-web
	uv run python -m http.server --directory web 8000

.PHONY: verify
verify: fmt-check lint portfolio-links test e2e

.PHONY: clean
clean:
	@rm -rf .pytest_cache .ruff_cache .playwright .playwright-artifacts test-results
	@rm -rf dist build web/.pytest_cache web/assets/py
	@find src tests scripts -type d -name __pycache__ -prune -exec rm -rf {} +
