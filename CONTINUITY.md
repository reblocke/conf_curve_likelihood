# Continuity ledger

Use this file to maintain continuity across coding sessions (human or agent).

## Current status

- Goal: Build the Wald Confidence Curve Explorer as a static GitHub Pages app with a Python numerical core staged into Pyodide.
- Last known good commit: 9340039
- Next step: Monitor future Pages deploys for the GitHub Actions Node 20 deprecation warnings and update action versions once GitHub publishes Node 24-ready releases.

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
- GitHub Pages now deploys successfully, but the current Pages actions still emit GitHub's Node 20 deprecation warnings

**Objective:**

Land the merged review-follow-up fixes and continue the release checkpoint.

**Plan:**

- eliminate non-JSON numeric payloads under extreme null/likelihood cases
- widen the x-grid when nulls or thresholds fall outside the default Wald span
- clear stale browser render/export state after failed recomputations
- push the fix branch through CI, then resolve the remaining Pages deployment blocker if possible

**Work completed:**

- changed the likelihood summary/log calculations to stay strictly JSON-serializable
- expanded `build_grid()` so distant null and threshold markers are included in the plotted range
- cleared cached browser response/plot/export state after input or compute failures
- added unit, integration, property, and browser regressions for the reviewed failure modes
- reran `make verify` successfully on the follow-up branch

**Verification:**

- `make verify`
- `uv run pytest -q tests/e2e/test_app.py::test_invalid_ratio_input_surfaces_validation_error tests/e2e/test_app.py::test_distant_markers_expand_the_x_axis_extent --browser chromium`

**Open questions / risks:**

- the app is deployed successfully on GitHub Pages, but the Pages workflow should be revisited before GitHub enforces Node 24-only JavaScript actions in June 2026
