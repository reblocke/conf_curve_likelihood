# Continuity ledger

Use this file to maintain continuity across coding sessions (human or agent).

## Current status

- Goal: Maintain the deployed Wald Confidence Curve Explorer and plan the next UX/statistics refinements, including correct default x-axis display for ratio measures.
- Last known good commit: 4a024c1 on `main`
- Next step: Decide how ratio measures should default to logarithmic display on the x-axis while preserving the current working-scale calculations and keeping issue #5 tracked separately.

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
