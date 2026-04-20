# Decisions

Use this file to record decisions that are hard to infer from the code alone.

## 2026-03-23: Static GitHub Pages app with Python source of truth

**Context:**

The repository started from a general scientific-programming template, but the target product is a browser-facing applet that reconstructs Wald confidence curves and relative likelihood curves from an estimate and confidence interval.

**Decision:**

Use a hybrid structure:

- `src/confcurve/` holds the numerical and contract logic as the Python source of truth.
- `web/` holds the static GitHub Pages app.
- `scripts/stage_web_python.py` copies the Python package into `web/assets/py/confcurve/` so Pyodide imports the same code that local tests exercise.

**Alternatives considered:**

- Plain JavaScript only: simpler runtime, but it would split the numerical source of truth away from the Python scientific workflow.
- Server-side Python app: incompatible with the chosen GitHub Pages deployment target.

**Consequences:**

- Local and browser calculations share one implementation.
- The repo keeps Python-first quality gates while still shipping a static web app.
- A staging step is required before browser and deployment checks.

## 2026-03-23: Prefer validated scientific/testing packages over custom numerical code

**Context:**

The user requested concise code that leans on well validated packages and a robust test suite.

**Decision:**

Use:

- `numpy` and `scipy` for numerical computation.
- Plotly.js for plotting and image export.
- `pytest`, `hypothesis`, `playwright`, and `pytest-playwright` for verification.

Browser bundles are pinned by exact version and integrity hash. Python dependencies are pinned through `uv.lock`.

**Alternatives considered:**

- Custom normal-CDF and plotting logic: less dependency weight, but higher correctness risk.
- Visual snapshot testing in CI: stronger regression coverage, but deferred for v1 to avoid excessive maintenance overhead.

**Consequences:**

- Core computations rely on battle-tested libraries.
- CI and local verification become heavier, especially for browser tests.
- Local dependency versions should track the selected Pyodide stack closely.

## 2026-04-19: Compact agent instructions with focused skills

**Context:**

The previous root instructions included broad working guidance and a continuity-ledger workflow.
That made recurring agent context large and easy to let drift from the actual repository commands.

**Decision:**

Use a short root `AGENTS.md` for project-specific rules and move recurring workflows into focused
repo-local skills under `.agents/skills/`. Durable decisions remain in `docs/DECISIONS.md` or ADRs
under `docs/adr/`.

**Consequences:**

- Agents get the same mandatory project constraints with less prompt overhead.
- Workflow guidance is more modular and easier to reuse across related repositories.
- The old `CONTINUITY.md` ledger is retired; it should not be treated as current repository state.
