# Integrated Wald Inference Workbench

> Looking for one specific task? Use the
> [focused Wald tools catalog](https://reblocke.github.io/wald-inference-tools/). This integrated
> workbench keeps compatibility, normalized likelihood, and repeated-study design-calibration
> views together for advanced side-by-side comparison.

This repository builds a static web app and Python package that reconstruct:

- a compatibility / confidence curve,
- a normalized Wald relative-likelihood curve, and
- point-estimate, null, user-supplied reference-threshold, and 80% power benchmark markers

from a 95% confidence interval and an optional validating point estimate.

The numerical source of truth is the released
[`wald-inference` package](https://github.com/reblocke/wald-inference-core).
`src/confcurve/` is the backward-compatible Python/browser adapter: it preserves the legacy
imports and `compute_curves()` payload contract while delegating core-owned calculations.
The deployed app lives in `web/` and loads generated, verified copies of both packages in the
browser through Pyodide.

Deployed app: [https://reblocke.github.io/conf_curve_likelihood/](https://reblocke.github.io/conf_curve_likelihood/)

The v0.2.0 integrated-workbench release is pinned to `wald-inference` v0.4.0. It preserves the
legacy numerical, Python, browser, and export contracts while adopting the portfolio's current
Core release.

## Choose a focused tool for one question

- [Compatibility curve](https://reblocke.github.io/compatibility-curve/) — candidate effects under
  an observed confidence-interval reconstruction.
- [Wald likelihood support](https://reblocke.github.io/wald-likelihood-support/) — normalized
  relative support and S-minus-2 summaries under that reconstruction.
- [Critical effect size](https://reblocke.github.io/critical-effect-size/) — exact fixed-SE
  detectability under a chosen future-study claim rule.
- [Type S/M calibrator](https://reblocke.github.io/type-s-m-calibrator/) — repeated-study sign and
  magnitude behavior conditional on assumed true effects and selection.
- [Precision guardrail planner](https://reblocke.github.io/precision-guardrail-planner/) —
  per-target and joint precision requirements under explicit design guardrails.

Observed-data panels condition on the reported estimate and CI; design panels condition on assumed
true effects and repeated-study behavior. Use this integrated interface only when comparing those
paradigms together is intentional.

## Related Wald tools

- [Portfolio catalog](https://reblocke.github.io/wald-inference-tools/)
- [Focused compatibility-curve app](https://reblocke.github.io/compatibility-curve/)
- [Integrated workbench](https://reblocke.github.io/conf_curve_likelihood/)
- [Source repository](https://github.com/reblocke/conf_curve_likelihood)
- Numerical source: [`wald-inference Core v0.1.1`](https://github.com/reblocke/wald-inference-core/releases/tag/v0.1.1)
- [Privacy and data path](https://github.com/reblocke/conf_curve_likelihood/blob/main/docs/migration/CURRENT_BEHAVIOR.md#privacy-and-data-path): entered numerical values stay in the browser; static CDNs still receive ordinary request metadata.

## What the app does

- accepts a 95% CI, effect type, optional point estimate, optional null, optional plausible display range, optional user-supplied reference thresholds/MCIDs, and ratio-axis spacing
- computes the Wald standardized distance on the appropriate working scale
- displays the corresponding compatibility curve and normalized relative-likelihood curve in both-panel, compatibility-only, or likelihood-only view modes
- highlights the reported 95% CI on compatibility-visible views and the evidential S−2 support interval on likelihood-visible views
- reports summary quantities such as the CI-implied estimate, reconstructed SE, 80% power benchmark markers for `alpha = 0.05` and `power = 0.80`, null relative likelihood, threshold-support comparisons, and the two-sided Wald p-value
- optionally computes design-calibration quantities - selected-claim probability, Type S wrong-sign probability, Type M magnitude exaggeration, and observed exaggeration - across candidate assumed true effects using a user-selected Wald claim rule
- supports design-only information multipliers and inverse precision targets for asking what approximate Wald SE or information multiplier would meet power, Type S, or Type M targets at an assumed true effect
- exports the current x-grid as CSV, the dashboard plot as PNG, and a figure-only manuscript PNG with a separate copyable caption

## What the app does not do

- it does not recover the exact model-based profile likelihood from the fitted model
- it does not infer the original study design, variance estimator, or sample-size model
- it does not validate whether the published interval was truly Wald-based beyond symmetry checks
- it does not treat Type S/M as posterior probabilities that the observed estimate is wrong; Type S/M are repeated-study operating characteristics under user-specified assumed true effects and a selected claim rule
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
Type M design calibration for ratio measures is also computed on the log working scale, not as direct inflation of the natural odds/risk/hazard ratio.

The optional plausible display range constrains only the plotted and exported x-grid. It does not change the CI-derived estimate, reconstructed standard error, null summaries, threshold-support summaries, 80% power benchmark markers, or reconstruction warnings.

The S−2 support interval is shown on the normalized Wald relative-likelihood panel as the effects with relative likelihood at least `exp(-2)` compared with the CI-implied estimate. Equivalently, the CI-implied estimate is no more than `exp(2)` or about `7.4x` as supported as values inside the interval.

The paired 80% power benchmark markers are Wald `alpha = 0.05`, `power = 0.80` benchmarks around the null. They are a design-interpretation aid related to critical-effect-size thinking, not a replacement for a study-specific critical-effect-size or power analysis. User-supplied reference thresholds/MCIDs are observed-display markers; design claim thresholds are separate selected-claim-rule inputs.

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
`make serve`, `make test`, `make e2e`, CI, and GitHub Pages all invoke the same
`make stage-web` prerequisite.

## Core dependency and browser staging

The locked dependency is the exact GitHub release artifact below; it is not `main`, a sibling
checkout, an editable path, or an unpinned Git reference.

| Item | Authority |
|---|---|
| Core version | `wald-inference` v0.4.0 |
| Release | <https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.0> |
| Release status observed 2026-07-30 | GitHub prerelease |
| Release commit | `fd7b24740122bed7ae07769674732c5e56c91277` |
| Wheel | <https://github.com/reblocke/wald-inference-core/releases/download/v0.4.0/wald_inference-0.4.0-py3-none-any.whl> |
| Wheel SHA-256 | `401a0cc2a182918764149eb03c79672217b647147c494215c83515fd609c7af6` |
| License | MIT |

`make stage-web` deterministically replaces the ignored `web/assets/py/` directory from the
locked environment. It stages `wald_inference` and `confcurve` and writes
`web/assets/py/manifest.json` with the app/core package versions, source commit, ordered file
metadata, per-file SHA-256 digests and byte counts, and an aggregate bundle SHA-256. The browser
validates the manifest schema, every file digest, and the aggregate digest before importing either
package. Stale files cannot survive replacement.

Generated Python is never edited or committed. A clean clone needs only this repository, `uv`, and
network access to the pinned release URL during the initial locked dependency install; no adjacent
`wald-inference-core` checkout is used. See
[ADR 0002](docs/adr/0002-released-core-and-generated-browser-stage.md) for the ownership, upgrade,
rollback, and compatibility policy.

### Frozen compatibility contract

The migration authority is the
[`pre-split-baseline-2026-07-29`](https://github.com/reblocke/conf_curve_likelihood/releases/tag/pre-split-baseline-2026-07-29)
release, with behavior source `830756ecb11b4e8161f8dfe1fc75afc346ef4467`. Its 22 B01–B08
cases freeze the `confcurve.__all__` compatibility surface, `compute_curves()` request/response
schema and ordering, warnings and errors, strict JSON, default UI behavior, views and overlays,
CSV/PNG exports, caption, and reviewer text. The fixture manifest SHA-256 is
`f54bb2d8311788c07adcf23fc9f038e35702449e4a77a474abea9411246cabcc`; the fixture-set
SHA-256 is `81c341b39e711caffc85a444f0c1e4bc1e2d00633474c82e720afeb60def3c4d`.
Migration comparisons use `rtol=1e-12`, `atol=1e-14`, and exact comparison for declared identity
fields. Any unexplained difference is a release blocker.

## Repository layout

- `src/confcurve/` – legacy compatibility API, browser payload contract, orchestration, and staging
  helpers
- `scripts/` – thin automation such as staging the Python package for the web app
- `tests/` – unit, property, integration, and Playwright end-to-end tests
- `tests/golden/` – source-stamped pre-split request/response and export-schema fixtures
- `tests/e2e/` – behavior-focused browser tests with shared Playwright helpers
- `web/` – static GitHub Pages site; `web/assets/py/` is generated and ignored
- `web/assets/app.js` – browser entrypoint for DOM state, event wiring, compute, and rerender orchestration
- `web/assets/config.js`, `formatters.js`, `runtime.js`, and `renderers.js` – browser configuration, display formatting, Pyodide loading, and HTML rendering helpers
- `web/assets/plot.js` and `plot-helpers.js` – Plotly rendering/export API and pure plotting helpers
- `docs/` – decisions, workflow notes, and guardrails

## Verification

- `make fmt` formats Python code with Ruff
- `make fmt-check` checks Ruff formatting
- `make lint` runs Ruff checks
- `make golden-check` verifies the frozen B01–B08 contract and numerical baseline
- `make test` runs non-E2E tests
- `make e2e` runs Playwright browser tests
- `make verify` runs staging, format check, lint, frozen parity, non-E2E tests, and E2E checks
- `make serve` regenerates the browser Python bundle before starting the local server

## Worked examples

- Additive example: mean difference 95% CI `0.11` to `0.73`, implied point estimate `0.42`, null `0`
- Ratio example: odds ratio 95% CI `1.2` to `2.7`, implied point estimate `1.8`, null `1`, natural-scale axis with logarithmic spacing by default, both-panel view by default, and optional plausible display range such as `0.9` to `1.1`
- Threshold example: add comma-separated reference values such as `0.8, 1.25` to compare user-defined thresholds against the CI-implied estimate and null under the same Wald reconstruction
- Design example: enable design calibration, choose a selected-claim rule, and set an information multiplier such as `4` to view fixed C-F panels for power, Type S, Type M, and observed exaggeration under a hypothetical SE equal to half the CI-implied SE; ratio design curves are display-capped at `10x` near the null while tables and exports retain uncapped values

## Documentation and citation

- `AGENTS.md` defines repo-specific engineering rules.
- `docs/DECISIONS.md` records architectural choices.
- `docs/adr/0002-released-core-and-generated-browser-stage.md` records the core dependency,
  staging, upgrade, and rollback decision.
- `docs/MAINTENANCE.md` defines the feature-freeze, compatibility, and future archival criteria.
- `docs/migration/` records the frozen pre-split behavior and portfolio migration contract.
- `docs/TYPE_SM_DESIGN_ANALYSIS.md` explains the optional Type S/M design-calibration layer.
- `CITATION.cff` provides software citation metadata and should be updated when release metadata changes.
- `CHANGELOG.md` records app release notes and exact core provenance.
- Source links used for app terminology and presentation notes:
  - [Zampieri et al., AJRCCM 2025](https://academic.oup.com/ajrccm/article/211/9/1610/8300617) for evidential likelihood, likelihood ratios, support, and S−2 intervals; retrieved 2026-04-23.
  - [Perugini et al., AMPS 2025](https://journals.sagepub.com/doi/10.1177/25152459251335298) for critical-effect-size values and design-interpretation rationale; retrieved 2026-04-23.
  - [Gelman & Carlin 2014](https://journals.sagepub.com/doi/abs/10.1177/1745691614551642) for Type S sign error, Type M magnitude/exaggeration ratio, and design calculations; retrieved 2026-06-14.

## Repository Notes

### Project Status

Maintained, feature-frozen integrated workbench. Supported changes are Core upgrades, correctness,
accessibility, security, browser compatibility, and documentation/portfolio-link maintenance. See
[Maintenance](docs/MAINTENANCE.md). No manuscript version is expected. Code and teaching examples
are repository-authored unless otherwise noted.

### Data and Reuse

No clinical data expected

### License

MIT License for repository code; see `LICENSE`. Third-party and publisher materials remain under their original terms.

### Contact

Maintainer: Brian Locke (`@reblocke`). Use GitHub issues or pull requests for repository-specific questions when the repository is public.

## Related Wald tools

- Choose a tool: [Wald inference tools catalog](https://reblocke.github.io/wald-inference-tools/)
- Closest adjacent tool:
  [Compatibility curve](https://reblocke.github.io/compatibility-curve/)
- Integrated workbench:
  [this hosted application](https://reblocke.github.io/conf_curve_likelihood/)
- App repository: [reblocke/conf_curve_likelihood](https://github.com/reblocke/conf_curve_likelihood)
- Numerical dependency:
  [wald-inference Core v0.4.0](https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.0)
- Privacy: calculations run locally in the browser; entered numerical values are not placed in URLs
  or sent to an application server.
