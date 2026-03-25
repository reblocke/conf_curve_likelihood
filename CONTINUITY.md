# Continuity ledger

Use this file to maintain continuity across coding sessions (human or agent).

## Current status

- Goal: Implement the parsimonious browser/UI fixes for ratio-axis spacing, threshold/grid-point controls, cutoff visibility, point-estimate copy, and README deployment/docs updates.
- Last known good commit: 5371685 on `main`
- Next step: Push the verified browser/UI fix set to `main`, then monitor the resulting CI and Pages runs.

## Open checkpoints

- Branch: `main`
- PR: #8 merged (`feat: make the Wald reconstruction CI-driven`)
- Expected gates:
  - local `make verify`: passed before merge on the feature branch
  - post-merge `CI` on `main`: passed (`23511197395`)
  - post-merge `Deploy Pages` on `main`: passed (`23511197402`)
  - live Pages smoke: confirmed the deployed HTML serves the new optional-estimate wording

## Session log

### 2026-03-24

**Objective:**

Resume the interrupted CI-driven/critical-markers implementation, audit the exact handoff point, and finish the merge/deploy checkpoint cleanly.

**Plan:**

- inspect git/PR/ledger state to find the interrupted checkpoint
- watch PR #8 to completion and merge it if green
- verify the `main` CI and Pages deploy after merge
- refresh the continuity ledger to the merged state

**Work completed:**

- confirmed the interrupted work was fully implemented on `codex/ci-driven-critical-markers` and already pushed as PR #8
- watched PR #8 checks through green (`test`, `e2e_chromium`, `e2e_webkit_smoke`) and merged it to `main`
- verified the merge commit was `4a024c1` and the remote feature branch was deleted
- verified post-merge `CI` and `Deploy Pages` both succeeded on `main`
- confirmed the live Pages site serves the new optional-estimate/cutoff copy from the merged build

**Verification:**

- `gh pr checks 8 --watch --interval 10`
- `gh run watch 23511197395`
- `gh run watch 23511197402`
- `curl -fsSL https://reblocke.github.io/conf_curve_likelihood/ | rg -n "Estimate \\(optional\\)|95% confidence interval and optional estimate|Show horizontal 90%, 95%, and 99% confidence guide lines"`

**Open questions / risks:**

- issue #5 remains open because GitHub's current Pages-specific actions still emit Node 20 deprecation warnings; this is upstream-blocked rather than an application defect

**Objective:**

Triage the GitHub review feedback on commit `1268f2f30b` and patch any still-live defects.

**Plan:**

- inspect the inline review comments on PR #8 directly from GitHub
- reproduce any reported failures against current `main`
- patch the midpoint/SE reconstruction if the overflow report is still real
- rerun focused verification, then rerun the non-E2E suite

**Work completed:**

- confirmed there was one substantive inline review comment on PR #8 and reproduced it on current `main`
- verified that `validate_inputs()` still rejected the valid additive CI `[-1e308, 1e308]` because midpoint inference overflowed on the working scale
- patched `src/confcurve/core.py` so working-scale midpoint, half-width, and side-width arithmetic avoid overflow for large opposite-signed finite bounds
- restaged the browser Python package into `web/assets/py/confcurve/`
- added a regression in `tests/test_core.py` covering the reviewed additive-edge case through `compute_curves()`

**Verification:**

- `uv run python - <<'PY' ... compute_curves({'effect_type': 'mean_difference', 'lower': -1e308, 'upper': 1e308, 'grid_points': 401}) ... PY`
- `uv run pytest -q tests/test_core.py -k "opposite_signed or additive_ci_only or large_additive_estimate or float_max_ratio_interval or extreme_additive_null"`
- `uv run ruff format --check src/confcurve/core.py tests/test_core.py`
- `uv run ruff check src/confcurve/core.py tests/test_core.py`
- `make test`

**Open questions / risks:**

- the next planned product refinement is still the ratio-measure x-axis display rule; this fix only addresses the reviewed overflow bug

### 2026-03-25

**Objective:**

Implement the requested browser/UI fixes for ratio-axis spacing, threshold/grid-point control separation, cutoff visibility, point-estimate copy, and README updates.

**Plan:**

- replace the ratio natural/working checkbox with a frontend-only axis-spacing control
- keep ratio labels on the natural scale while switching Plotly between logarithmic and linear spacing
- separate the threshold and grid-point controls visually
- tighten render error handling and make the upper-panel cutoff guides more legible
- update the README and browser tests to match the new UI

**Work completed:**

- replaced the ratio-only checkbox with an `Axis spacing` select that defaults to `Logarithmic` and is hidden for additive measures
- changed the browser payload path so ratio measures always request natural-scale labels from the backend while the frontend controls only the Plotly axis type
- updated Plotly rendering to use log spacing for ratio measures by default, allow linear spacing as a display option, preserve natural-scale labels, and keep both y-axis titles visible
- separated `Clinical thresholds` and `Grid points` into distinct control sections and moved the grid-point output next to its own label
- changed UI copy from `Estimate` to `Point Estimate` and clarified that cutoff guides belong to the upper compatibility panel
- added a post-render guard so an empty Plotly surface becomes a visible status-card error
- refreshed the README with the deployed site URL and the updated CI-driven / natural-labels-with-log-spacing methodology wording
- updated Chromium E2E coverage for ratio-axis type changes, control separation, cutoff behavior, and y-axis title visibility

**Verification:**

- `uv run ruff format --check tests/e2e/test_app.py`
- `uv run ruff check tests/e2e/test_app.py`
- `make test`
- `make e2e`
- `uv run pytest -q tests/e2e/test_app.py::test_initial_render_loads_pyodide_and_plots -m e2e --browser webkit --tracing retain-on-failure --video retain-on-failure --screenshot only-on-failure --output test-results`

**Open questions / risks:**

- the backend still exposes `display_natural_axis` internally even though the main UI now always keeps ratio labels on the natural scale; that is intentional for parsimony, but it is now effectively an internal compatibility detail

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

**Objective:**

Close the remaining finite-payload overflow edge case and continue the actionable Node 24 maintenance stage.

**Plan:**

- cap grid expansion before it can overflow the plotted payload
- make extreme null summaries explicitly overflow-safe for the browser JSON bridge
- upgrade the CI artifact-upload action to the latest official Node 24 runtime release
- push the branch through CI and keep the Pages-specific Node 20 warning tracked upstream

**Work completed:**

- reproduced the Codex review finding that extreme finite nulls could still generate `nan`/`inf` payloads
- capped grid span growth to keep `linspace`, standardized distances, and natural-axis back-transforms finite
- made extreme null summary fields report overflow with JSON-safe `null` values instead of non-finite floats
- added regressions for extreme additive and ratio cases that now pass strict `json.dumps(..., allow_nan=False)`
- upgraded CI artifact uploads from `actions/upload-artifact@v4` to `@v7`
- updated issue #5 with the current official release status of the Pages-related GitHub Actions

**Verification:**

- `make verify`
- `uv run python - <<'PY' ... json.dumps(response, allow_nan=False) ... PY` for the extreme additive and ratio reproductions

**Open questions / risks:**

- the Pages-specific actions (`configure-pages`, `deploy-pages`, `upload-pages-artifact`) are already on their latest official releases, so the remaining Node 20 warnings are upstream-blocked for now

**Objective:**

Address the remaining span/headroom review findings on commit `14d360ba9f` and re-check the outstanding Pages-maintenance step.

**Plan:**

- clamp grid spans against the estimate's remaining finite headroom on the working scale
- make natural-axis boundary rendering finite when ratio grids extend past `float.max`
- add focused regressions for large additive estimates and ratio estimates at `float.max`
- confirm whether issue #5 is still actionable with the latest official Pages action releases

**Work completed:**

- reproduced the review-reported overflow for a large additive estimate and the `Maximum span must be positive` failure at a ratio estimate of `float.max`
- capped `max_safe_grid_span()` by the estimate's remaining `±float.max` headroom on the working scale
- made `build_grid()` return a degenerate finite grid instead of hard-failing when the safe span collapses to zero
- clipped natural-axis ratio displays at the exact largest finite float while keeping the working-scale calculations unchanged
- added unit and integration regressions for both edge cases and reran the staged browser package
- rechecked the latest official Pages action releases and their published `action.yml` metadata; `configure-pages@v5.0.0` and `deploy-pages@v4.0.5` still run on `node20`, so issue #5 remains upstream-blocked

**Verification:**

- `make verify`
- `uv run pytest tests/test_core.py tests/integration/test_contract_response.py -q`
- `uv run python - <<'PY' ... compute_curves(...) ... json.dumps(..., allow_nan=False) ... PY` for the large-additive and `float.max` ratio reproductions

**Open questions / risks:**

- ratio estimates at the natural-axis ceiling necessarily flatten the right tail against `float.max`; the app now warns explicitly, but that display remains a numeric-boundary artifact rather than a fully faithful natural-scale view
- issue #5 is still pending upstream because GitHub's latest Pages-specific JavaScript actions continue to publish `using: node20`
