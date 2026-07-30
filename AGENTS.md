# Codex AGENTS

## Purpose
- This repository is the backward-compatible integrated web app for reconstructing Wald compatibility/confidence curves and normalized Wald relative-likelihood displays from published estimates and confidence intervals.
- Released `wald-inference` is the numerical source of truth. The local `confcurve` package owns compatibility aliases, browser payloads, app-specific orchestration, and staging.
- The static GitHub Pages app lives in `web/` and imports generated `wald_inference` and `confcurve` packages through Pyodide.
- Optimize for correctness, readability, reproducibility, and only then measured performance.

## Repo Map
- `src/confcurve/` - compatibility API, data models, staging helpers, and browser contract.
- `web/` - static browser app and browser ES modules; generated Python lives under ignored `web/assets/py/`.
- `scripts/stage_web_python.py` - stages the locked installed core and local adapter and generates `web/assets/py/manifest.json`.
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
- Never implement or copy a Wald formula in `confcurve`; add a missing numerical primitive and release it in `wald-inference-core` first.
- Pin core upgrades to an exact released artifact and checksum. Review the upstream changelog, then rerun legacy API, frozen contract, strict-JSON, staging, and browser validation before adoption.
- Keep `confcurve` wrappers thin and behavior-preserving. Browser payload assembly, display choices, warnings, and exports remain local app concerns.
- Run `make stage-web` rather than editing generated Python under `web/assets/py/`. Generated stage output must remain ignored and reproducible from a clean checkout with no sibling repository.
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
