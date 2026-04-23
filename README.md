# Wald Confidence Curve Explorer

This repository builds a static web app and Python package that reconstruct:

- a compatibility / confidence curve,
- a normalized Wald relative-likelihood curve, and
- point-estimate, null, user-supplied threshold, and design-threshold markers

from a 95% confidence interval and an optional validating point estimate.

The numerical source of truth lives in `src/confcurve/`. The deployed app lives in `web/` and loads that same Python package in the browser via Pyodide.

Deployed app: [https://reblocke.github.io/conf_curve_likelihood/](https://reblocke.github.io/conf_curve_likelihood/)

## What the app does

- accepts a 95% CI, effect type, optional point estimate, optional null, optional plausible display range, optional user-supplied clinical/reference thresholds, and ratio-axis spacing
- computes the Wald standardized distance on the appropriate working scale
- displays the corresponding compatibility curve and normalized relative-likelihood curve in both-panel, compatibility-only, or likelihood-only view modes
- highlights the reported 95% CI on compatibility-visible views and the evidential S−2 support interval on likelihood-visible views
- reports summary quantities such as the CI-implied estimate, reconstructed SE, design-threshold markers for `alpha = 0.05` and `power = 0.80`, null relative likelihood, threshold-support comparisons, and the two-sided Wald p-value
- exports the current x-grid as CSV, the dashboard plot as PNG, and a figure-only manuscript PNG with a separate copyable caption

## What the app does not do

- it does not recover the exact model-based profile likelihood from the fitted model
- it does not infer the original study design or variance estimator
- it does not validate whether the published interval was truly Wald-based beyond symmetry checks
- it does not provide clinical decision support or medical-device functionality; threshold fields are user-defined reference markers for interpreting the reconstructed display

Use the wording “normalized Wald relative likelihood” or “approximate profile-likelihood-style view under Wald assumptions” consistently. Avoid presenting the likelihood panel as exact fitted-model profile likelihood.

## Working scales

- Additive measures use the natural scale:
  - mean difference
  - risk difference
  - rate difference
  - regression coefficient
- Ratio measures use the log scale for computation:
  - odds ratio
  - risk ratio
  - hazard ratio
  - incidence rate ratio
  - ratio of means

For ratio measures, the app computes on the log scale, labels the x-axis on the natural ratio scale, and can display that natural-scale axis with logarithmic or linear spacing.

The optional plausible display range constrains only the plotted and exported x-grid. It does not change the CI-derived estimate, reconstructed standard error, null summaries, threshold-support summaries, design-threshold markers, or reconstruction warnings.

The S−2 support interval is shown on the normalized Wald relative-likelihood panel as the effects with relative likelihood at least `exp(-2)` compared with the CI-implied estimate. Equivalently, the CI-implied estimate is no more than `exp(2)` or about `7.4x` as supported as values inside the interval.

The paired design-threshold markers are Wald `alpha = 0.05`, `power = 0.80` benchmarks around the null. They are a design-interpretation aid related to critical-effect-size thinking, not a replacement for a study-specific critical-effect-size or power analysis.

## Quickstart

1. Create the environment.

```bash
uv sync --locked
```

2. Install Playwright browsers for browser tests.

```bash
uv run playwright install chromium webkit
```

3. Run the full verification suite.

```bash
make verify
```

4. Serve the app locally.

```bash
make serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Repository layout

- `src/confcurve/` – Python numerical core, payload contract, and staging helpers
- `scripts/` – thin automation such as staging the Python package for the web app
- `tests/` – unit, property, integration, and Playwright end-to-end tests
- `tests/e2e/` – behavior-focused browser tests with shared Playwright helpers
- `web/` – static GitHub Pages site
- `web/assets/app.js` – browser entrypoint for DOM state, event wiring, compute, and rerender orchestration
- `web/assets/config.js`, `formatters.js`, `runtime.js`, and `renderers.js` – browser configuration, display formatting, Pyodide loading, and HTML rendering helpers
- `web/assets/plot.js` and `plot-helpers.js` – Plotly rendering/export API and pure plotting helpers
- `docs/` – decisions, workflow notes, and guardrails

## Verification

- `make fmt` formats Python code with Ruff
- `make fmt-check` checks Ruff formatting
- `make lint` runs Ruff checks
- `make test` runs non-E2E tests
- `make e2e` runs Playwright browser tests
- `make verify` runs staging, format check, lint, tests, and E2E checks

## Worked examples

- Additive example: mean difference 95% CI `0.11` to `0.73`, implied point estimate `0.42`, null `0`
- Ratio example: odds ratio 95% CI `1.2` to `2.7`, implied point estimate `1.8`, null `1`, natural-scale axis with logarithmic spacing by default, both-panel view by default, and optional plausible display range such as `0.9` to `1.1`
- Threshold example: add comma-separated reference values such as `0.8, 1.25` to compare user-defined thresholds against the CI-implied estimate and null under the same Wald reconstruction

## Documentation and citation

- `AGENTS.md` defines repo-specific engineering rules.
- `docs/DECISIONS.md` records architectural choices.
- `CITATION.cff` provides software citation metadata and should be updated when release metadata changes.
- Source links used for app terminology and presentation notes, retrieved 2026-04-23:
  - [Zampieri et al., AJRCCM 2025](https://academic.oup.com/ajrccm/article/211/9/1610/8300617) for evidential likelihood, likelihood ratios, support, and S−2 intervals.
  - [Perugini et al., AMPS 2025](https://journals.sagepub.com/doi/10.1177/25152459251335298) for critical-effect-size values and design-interpretation rationale.
