# Wald Confidence Curve Explorer

This repository builds a static web app that reconstructs:

- a confidence / compatibility curve,
- an approximate profile likelihood under Wald assumptions, and
- critical effect markers for `alpha = 0.05` and `power = 0.80`

from a 95% confidence interval and an optional validating point estimate.

The numerical source of truth lives in `src/confcurve/`. The deployed app lives in `web/` and loads that same Python package in the browser via Pyodide.

## What the app does

- accepts a 95% CI, effect type, optional point estimate, optional null, and optional clinical thresholds
- computes the Wald standardized distance on the appropriate working scale
- displays the corresponding confidence curve and normalized relative likelihood curve
- reports summary quantities such as the CI-implied estimate, reconstructed SE, critical effect markers, null relative likelihood, and two-sided Wald p-value

## What the app does not do

- it does not recover the exact model-based profile likelihood from the fitted model
- it does not infer the original study design or variance estimator
- it does not validate whether the published interval was truly Wald-based beyond symmetry checks

Use the wording “approximate profile likelihood under Wald assumptions” consistently. Avoid presenting the lower panel as exact.

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

For ratio measures, the app computes on the log scale and can display the x-axis back on the natural scale.

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
- `tests/` – unit, property, integration, and end-to-end tests
- `web/` – static GitHub Pages site
- `docs/` – decisions, workflow notes, and guardrails

## Verification

- `make fmt` formats Python code with Ruff
- `make lint` runs Ruff checks
- `make test` runs non-E2E tests
- `make e2e` runs Playwright browser tests
- `make verify` runs staging, format check, lint, tests, and E2E checks

## Worked examples

- Additive example: 95% CI `0.11` to `0.73`, implied estimate `0.42`, null `0`
- Ratio example: odds ratio 95% CI `1.2` to `2.7`, implied estimate `1.8`, null `1`

## Documentation and citation

- `AGENTS.md` defines repo-specific engineering rules.
- `docs/DECISIONS.md` records architectural choices.
- `CITATION.cff` should be updated with final author and release metadata before a public release.
