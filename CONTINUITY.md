# Continuity ledger

Use this file to maintain continuity across coding sessions (human or agent).

## Current status

- Goal: Build the Wald Confidence Curve Explorer as a static GitHub Pages app with a Python numerical core staged into Pyodide.
- Last known good commit: d4ce951
- Next step: Commit and open the implementation PR from `codex/wald-confcurve-impl`.

## Session log

### 2026-03-23

**Objective:**

Realign the starter repository into the confidence-curve app repository and implement the first end-to-end version.

**Plan:**

- replace starter-specific docs, package structure, and CI assumptions
- implement the validated numerical core with `numpy` and `scipy`
- wire the static web UI to Pyodide and Plotly
- add unit, property, integration, and browser tests

**Work completed:**

- created the `codex/wald-confcurve-applet` branch
- removed the conflicting starter pipeline and Stata codepaths
- added the static `web/` shell with pinned Plotly and Pyodide assets
- rewrote the top-level project framing and decision log for the app
- implemented the numerical core with `numpy` and `scipy`
- wired the browser UI to Pyodide and Plotly
- added unit, property, integration, and Playwright browser tests
- verified local Chromium E2E, WebKit smoke, and `make verify`

**Verification:**

- `make verify`
- `uv run pytest -q tests/e2e/test_app.py::test_initial_render_loads_pyodide_and_plots -m e2e --browser webkit --tracing retain-on-failure --video retain-on-failure --screenshot only-on-failure --output test-results`

**Open questions / risks:**

- browser runtime performance still depends on Pyodide + SciPy startup cost, though local smoke tests passed
- the implementation branch still needs to be pushed and checked in GitHub Actions
