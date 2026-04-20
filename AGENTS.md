# Codex AGENTS

## Purpose
- This repository is a Python-first scientific web app for reconstructing Wald compatibility/confidence curves and normalized Wald relative-likelihood displays from published estimates and confidence intervals.
- The Python package is `confcurve`; the static GitHub Pages app lives in `web/` and imports staged Python through Pyodide.
- Optimize for correctness, readability, reproducibility, and only then measured performance.

## Repo Map
- `src/confcurve/` - numerical core, data models, staging helpers, and browser contract.
- `web/` - static browser app, browser ES modules, and staged Python package under `web/assets/py/confcurve/`.
- `scripts/stage_web_python.py` - copies the package source into the browser app.
- `tests/` - unit, integration, property, and Playwright E2E tests.
- `docs/` - decisions, workflow notes, and scientific/data-management documentation.
- `.agents/skills/` - focused local workflows for recurring agent tasks.

## Commands
- Setup: `uv sync --locked`
- Stage browser Python: `make stage-web`
- Format: `make fmt`
- Format check: `make fmt-check`
- Lint: `make lint`
- Unit/integration/property tests: `make test`
- Browser E2E tests: `make e2e`
- Full verification: `make verify`
- Local web app: `make serve`

## Authority
1. User request and any study/protocol requirements.
2. `README.md`, `docs/DECISIONS.md`, `docs/PRINCIPLES.md`, and this file.
3. Existing code and tests.

If implementation and documentation disagree, preserve behavior unless the task explicitly changes it, then record the decision in `docs/DECISIONS.md` or a new ADR under `docs/adr/`.

## Working Rules
- Before non-trivial edits, state assumptions, ambiguities, tradeoffs, a brief plan, risks, and verification commands.
- Keep changes small and directly tied to the request; do not make drive-by refactors.
- Keep `src/confcurve/` as the calculation source of truth; run staging rather than hand-editing duplicated Python under `web/assets/py/confcurve/`.
- Use `uv` with `pyproject.toml` and `uv.lock`; do not add parallel dependency managers.
- Use Ruff only for formatting/linting.
- Do not commit external artifacts without provenance and licensing notes.

## Skill Triggers
- Planning a non-trivial change: `.agents/skills/implementation-strategy/SKILL.md`.
- Verifying a code change: `.agents/skills/code-change-verification/SKILL.md`.
- Updating docs after behavior/workflow changes: `.agents/skills/docs-sync/SKILL.md`.
- Preparing PR text: `.agents/skills/pr-draft-summary/SKILL.md`.
- Reviewing numerical/statistical behavior: `.agents/skills/scientific-validation/SKILL.md`.
- Changing the static browser app or Pyodide staging: `.agents/skills/static-browser-pyodide-verification/SKILL.md`.
- Reviewing clinical/public wording, privacy, or provenance: use the matching focused skill in `.agents/skills/`.

## Done Criteria
- Relevant tests pass locally.
- Browser-facing package changes are staged and verified.
- Decisions, assumptions, and public-copy implications are documented when they change.
- The final report names changed files, verification commands, and any remaining risks.
