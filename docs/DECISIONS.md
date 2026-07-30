# Decisions

## 2026-07-30: Replace Core v0.4.0 with corrective release v0.4.1

The independent portfolio review identified invalid edge behavior in Core v0.4.0: non-monotone
threshold precision bracketing, cancellation in pairwise support ratios, and unrepresentable
ratio-scale exponential underflow. Adopt the exact released `wald-inference` v0.4.1 wheel, commit
`f4613177b6dc81d194aa70762152de2bfa86663b`, SHA-256
`d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b`.

The integrated workbench remains feature-frozen. The upgrade does not authorize new Core fields,
an app-local solver, tolerance widening, or changes to the frozen B01–B08 contract.

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

## 2026-04-19: Keep the browser entrypoint thin and split modules by responsibility

**Context:**

The static app grew to include Pyodide loading, request construction, summary rendering, view modes,
Plotly rendering, CSV export, dashboard PNG export, and manuscript PNG export. Keeping all browser
logic in a single file made behavior-preserving changes harder to review.

**Decision:**

Keep `web/index.html` importing only `web/assets/app.js`, and let `app.js` statically import focused
ES modules:

- `config.js` for browser constants and defaults.
- `formatters.js` for display text and number formatting.
- `runtime.js` for Pyodide loading and local package installation.
- `renderers.js` for summaries, commentary, warnings, captions, plot keys, and CSV generation.
- `plot.js` for the public Plotly rendering/export API.
- `plot-helpers.js` for pure Plotly layout, axis, marker, direct-label, and annotation helpers.

**Consequences:**

- The deployed app remains a static GitHub Pages site with `app.js` as the only HTML entrypoint.
- Browser behavior can be reviewed in smaller files without changing the Python contract or Wald
  formulas.
- E2E tests are split by behavior to keep browser coverage discoverable.

## 2026-04-23: Use the evidential S−2 definition for likelihood interval overlays

**Context:**

The app added a likelihood-panel overlay for an evidential support interval. The phrase "S2
interval" could be confused with a 2:1 likelihood interval or with S-value terminology.
The requested source was Zampieri et al., AJRCCM 2025
([article URL](https://academic.oup.com/ajrccm/article/211/9/1610/8300617), retrieved
2026-04-23).
The bottom-of-app source links also cite Perugini et al., AMPS 2025
([article URL](https://journals.sagepub.com/doi/10.1177/25152459251335298), retrieved
2026-04-23) for critical-effect-size values and design-interpretation rationale.

**Decision:**

Use the article's evidential S−2 definition: candidate effects remain inside the interval when
their support versus the MLE is no less than −2. In the app's normalized Wald likelihood, this
means `relative_likelihood >= exp(-2)`, so the CI-implied estimate is no more than `exp(2)` or
about `7.4x` as supported as interval values. Because
`log(relative_likelihood) = -0.5 * z^2`, the exact Wald endpoints are
`estimate_working +/- 2 * working_scale_se`.

**Consequences:**

- The app does not use `relative_likelihood >= 0.5` for this overlay; that would be a separate
  2:1 likelihood interval.
- The S−2 overlay is explanatory plot metadata and does not change summaries, reconstruction
  formulas, CSV export schema, or default inputs.
- The paired 80% power benchmark markers remain the app's Wald `alpha = 0.05`, `power = 0.80`
  benchmarks around the null. The critical-effect-size source is cited as related rationale, not
  as a claim that the app implements that article's alpha-only critical-effect-size calculations.
- Source provenance is recorded here and summarized in `README.md`; no external figures, tables,
  or substantial source text are copied into the repository.

## 2026-06-13: Add Type S/M design calibration as a separate repeated-study layer

**Context:**

The app now supports optional design calibration from the same CI-implied Wald standard error used
for the observed compatibility and relative-likelihood reconstruction. The design layer computes
power, Type S wrong-sign probability, Type M magnitude exaggeration, and observed exaggeration across
candidate assumed true effects.

**Decision:**

Keep Type S/M calculations in `src/confcurve/` as Python numerical code and expose them through the
existing browser JSON contract. For the MVP, support only the one-parameter normal/Wald model with a
two-sided `p < alpha` selected-claim rule. Compute Type M on the working-scale distance from the null;
for ratio measures this means the log scale. Return JSON `null` and UI blanks for Type S/M and
observed exaggeration at or very near the null.

Design plausible true-effect ranges are display metadata only. They may shade the design panel, but
they do not change the observed x-grid, confidence reconstruction, p-value curve, relative-likelihood
curve, or CSV observed columns.

**Alternatives considered:**

- JavaScript-only Type S/M calculations: simpler UI wiring, but it would split scientific formulas away
  from the tested Python source of truth.
- Selection-rule abstraction for one-sided or MCID-conditioned claims in the MVP: useful later, but too
  much surface area before the two-sided rule is stable and tested.
- Reporting Type S as `0.5` at the null: mathematically tempting under symmetric tails, but misleading
  for "wrong sign" because the true-effect direction is undefined at the null.

**Consequences:**

- Existing observed-data behavior remains the default when design calibration is disabled.
- Browser-facing Python must include `design.py` in the staging list and must be restaged before browser
  tests or deployment.
- Public wording must keep the observed-evidence layer separate from the repeated-study design layer
  and avoid presenting Type S/M as posterior probabilities or clinical decision guidance.

## 2026-06-13: Extend design calibration with precision scenarios and selected-claim rules

**Context:**

The original Type S/M ticket pack deferred precision scenarios and selection-rule extensibility until
after the MVP two-sided design layer was stable. Those extensions are useful for grant/sample-size
critique and for teaching how Type S/M depend on the rule that defines a selected claim.

**Decision:**

Add a tested selected-claim rule abstraction in `src/confcurve/design.py` and expose six Wald rules:

- two-sided `p < alpha` against the null,
- one-sided positive `p < alpha`,
- one-sided negative `p < alpha`,
- CI at selected alpha excludes the null in the selected claim direction,
- estimate exceeds a claim threshold / MCID and two-sided `p < alpha`,
- CI at selected alpha excludes a claim threshold / MCID.

Add design-only information multipliers, where `se_design = se_current / sqrt(multiplier)`, and inverse
precision targets that solve for the approximate Wald SE, 95% CI width, and information multiplier
needed to meet requested power, Type S, or Type M targets at a selected assumed true effect.

Threshold-conditioned rules require an explicit user-supplied threshold above the null for positive
claims and below the null for negative claims. Precision targets use the currently selected claim
rule, direction, threshold, alpha, and target true effect.

**Alternatives considered:**

- Keep selection rules as documentation-only roadmap: simpler, but leaves precision targets tied to
  only the default two-sided rule and makes later rule support harder to verify.
- Implement precision targets only for two-sided `p < alpha`: less UI and testing work, but duplicates
  the design formulas and risks inconsistent behavior once rule selection is added.

**Consequences:**

- Observed confidence, compatibility, likelihood, display-range, CSV observed columns, and export
  behavior remain unchanged when design calibration is disabled.
- Information multipliers affect only the design block and design panel, not observed reconstruction.
- Precision-target results may be blank with warnings when no finite meaningful solution is available.
- Public wording must describe these as repeated-study Wald design calculations, not clinical guidance
  or posterior probabilities.

## 2026-06-14: Visually separate observed evidence from design calibration

**Context:**

The optional design panel uses the same displayed x-values as the observed compatibility and
likelihood panels, but the interpretation changes. In panels A/B, x-values are candidate effect
sizes evaluated against the observed CI-derived Wald reconstruction. In panel C, x-values are
assumed true effects used to compute repeated-study operating characteristics.

**Decision:**

Keep all panels in one Plotly figure with a shared numeric x-range, but visually separate the
observed-data zone from the design-calibration zone. Panel titles, hover text, and the bottom x-axis
title must state that panel C treats x as the assumed true effect. Rename the former
"design-threshold" markers to "80% power benchmarks" and reserve "claim threshold" for the
user-entered selected-claim-rule threshold.

**Consequences:**

- The plot remains directly comparable across panels without implying that panel C conditions on the
  observed data in the same way as panels A/B.
- Reference thresholds/MCIDs, claim thresholds, and assumed true-effect scenarios must be labeled as
  separate concepts in the UI and docs.

## 2026-06-14: Show all design metrics in separate panels

**Context:**

The metric selector made panel C switch between power, Type S, Type M, and observed exaggeration.
After separating observed evidence from design calibration, hiding three design metrics behind a
selector made the figure harder to compare and obscured that all metrics share the same assumed-true
x-axis interpretation.

**Decision:**

When design calibration is enabled, plot all four design operating-characteristic metrics as fixed
panels C-F: selected-claim probability, Type S probability, Type M exaggeration, and observed
exaggeration if true. Type M and observed exaggeration may be unbounded near the null, so their plot
traces omit values above `10x` and use capped y-axes for readability. This cap applies only to the
rendered curves, not to the JSON contract, scenario tables, reviewer text, or CSV exports.

**Consequences:**

- The design figure is taller but no longer requires the reader to discover metrics through a
  dropdown.
- Ratio design panels may show intentional gaps near the null; warnings explain that those omitted
  values exceed the display cap.

## 2026-06-14: Label ratio design panels as x-fold exaggeration

**Context:**

Panels E and F both plot ratio-valued operating characteristics that can grow near the null. Their
long y-axis titles overlapped in the stacked design-panel layout, and the display needed a clearer
visual cue for common magnitude-overestimation thresholds.

**Decision:**

Use shorter x-fold y-axis titles for the ratio panels, add a subtle `2x` horizontal guide, and label
visible ratio ticks as `1x`, `2x`, `5x`, and `10x` where they fall inside the active y-range. Keep the
existing display-only `10x` omission rule. Cite Gelman and Carlin (2014) as the primary Type S/M
methodology reference for sign error, magnitude/exaggeration ratio, and design calculations.

**Consequences:**

- The plotted y-axis now communicates magnitude overestimation directly without changing any JSON,
  CSV, scenario-table, or reviewer-text values.
- The `2x` guide is a visual reference only; it is not a selected-claim rule, precision target, or
  validation threshold.

## 2026-07-29: Canonicalize public metadata under Brian Locke

**Context:**

Public repository metadata used conflicting identities: the Python package and software citation
named Reed Blocke, the README named Brian W. Locke, and the MIT license retained an unresolved
copyright-holder placeholder. A single authoritative identity is required before partitioning and
releasing related repositories.

**Decision:**

Use `Brian Locke` as the canonical public author and maintainer name in package metadata, software
citation metadata, and repository documentation. Retain the MIT License and set its copyright notice
to `Copyright (c) 2026 Brian Locke`.

**Consequences:**

- Future repository metadata should use `Brian Locke` unless a later explicit decision supersedes
  this one.
- The existing `@reblocke` GitHub account and repository URLs remain unchanged.
- This metadata correction does not change scientific calculations, browser behavior, public APIs,
  package versions, or release dates.

## 2026-07-29: Supersede the integrated numerical source with a released core

**Context:**

The portfolio split requires the integrated workbench and future focused applets to use one
versioned numerical implementation while the existing Python and browser contracts remain stable.
The earlier 2026-03-23 staging decision assumed that `src/confcurve/` owned the formulas and that
its generated browser copy could be committed.

**Decision:**

Adopt the exact released `wald-inference` v0.1.1 wheel as the numerical source of truth.
`confcurve` becomes the compatibility and browser-contract adapter. Generate and verify both
packages under ignored `web/assets/py/` through the single `make stage-web` path used locally and by
CI, Pages, and releases. The complete dependency, manifest, upgrade, compatibility, and rollback
policy is [ADR 0002](adr/0002-released-core-and-generated-browser-stage.md).

**Consequences:**

- The 2026-03-23 formula-ownership and committed-stage assumptions are superseded; its choice of a
  Python-first static Pyodide app remains in force.
- New or changed numerical behavior begins in `wald-inference-core` and reaches this app only through
  an exact reviewed release.
- Browser payload assembly, UI behavior, copy, exports, and the existing Pages URL remain owned here.
- Generated Python files are ignored build artifacts and must leave tracked Git state clean.

## 2026-07-30: Maintain this repository as the integrated Wald inference workbench

**Context:**

Five focused applets and a question-based catalog now provide clearer entry points for single
inferential tasks. This repository still provides a legitimate advanced use case: comparing
observed-data compatibility/relative-support views with assumed-truth repeated-study design views
in one backward-compatible interface.

**Decision:**

Keep the repository name, Pages URL, `confcurve` package, browser payload, defaults, views, and
exports unchanged. Present the product as the maintained integrated Wald inference workbench,
recommend the catalog for single questions, and feature-freeze the workbench except for exact Core
upgrades, correctness, accessibility, security, browser compatibility, and documentation/link
maintenance. Adopt the exact released `wald-inference` v0.4.0 wheel, SHA-256
`401a0cc2a182918764149eb03c79672217b647147c494215c83515fd609c7af6`, only after frozen parity
passes.

**Consequences:**

- Focused-app-only features and new paradigms normally belong outside this repository.
- Core additions are not exposed automatically through the legacy adapter.
- Observed panels continue to describe candidate effects under the reported-data reconstruction;
  design panels continue to describe assumed true effects under repeated-study behavior.
- Future archival is a separate human decision governed by `docs/MAINTENANCE.md`.
