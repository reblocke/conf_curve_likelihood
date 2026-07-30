# Wald Applet Portfolio Target

## Goal

Partition the integrated Wald app into focused static applets backed by one versioned
pure-Python numerical package while preserving the existing integrated URL, browser
contract, and `confcurve` compatibility surface.

The split is behavior-preserving first and task-specific second. It separates two distinct
conditioning statements:

- **Observed evidence:** candidate effects are evaluated against an estimate and 95% CI
  reconstructed under a one-parameter Wald model.
- **Repeated-study design:** candidate effects are assumed true values that generate future
  study results under an explicit selected-claim rule.

Sharing a working scale does not make those interpretations interchangeable.

## Target repositories

| Repository | Responsibility |
|---|---|
| `reblocke/wald-inference-core` | Versioned pure-Python numerical source of truth |
| `reblocke/scientific-applet-template` | Reusable static Pages/Pyodide engineering scaffold with no statistical formulas |
| `reblocke/compatibility-curve` | Observed-data Wald compatibility/confidence curve |
| `reblocke/wald-likelihood-support` | Approximate normalized Wald relative-likelihood and support comparisons |
| `reblocke/critical-effect-size` | Detectability, exact Wald power, and critical-effect-size interpretation |
| `reblocke/type-s-m-calibrator` | Forward selected-claim, Type S, and Type M calibration |
| `reblocke/precision-guardrail-planner` | Inverse precision and information requirements |
| `reblocke/wald-inference-tools` | Static catalog and question-routing guide |
| `reblocke/conf_curve_likelihood` | Backward-compatible integrated workbench consuming the shared core |

Repository existence must be checked immediately before creation. An existing target is
reconciled, not overwritten.

## Ownership boundaries

### Numerical core

`wald-inference-core` owns:

- effect specifications and identity/log working-scale transformations;
- 95% CI reconstruction and standard-error estimation;
- standardized Wald distance, compatibility, and normalized relative likelihood;
- support intervals and pairwise support comparisons;
- the legacy 80% z-sum benchmark and later approved exact detectability functions;
- the six supported selected-claim rules;
- Type S, Type M, and selected-claim probabilities;
- information scaling and inverse precision solvers; and
- numerical validation, finite-value protection, and scientific tests.

It does not own browser payload schemas, DOM state, Plotly configuration, public prose, CSV
column selection, Pages workflows, or app-specific defaults.

### Focused and integrated apps

Each app owns its narrow request/response adapter, input parsing, presentation, plot/table
construction, limitations text, exports, and browser tests. It may call the core through a
thin adapter. It may not copy, rederive, or independently maintain a core-owned formula.

The integrated workbench remains available at its existing repository and Pages URL. It is
not renamed, archived, or stripped of features during this migration.

### Engineering template

`scientific-applet-template` owns reusable build and browser infrastructure: locked
environments, Pyodide staging, Plotly/export helpers, accessible form/error patterns,
Ruff/pytest/Hypothesis/Playwright wiring, CI, Pages, and documentation templates. It
contains no domain formulas and is not a runtime dependency of released apps.

### Catalog

`wald-inference-tools` explains which question each tool answers and links to deployed
sites. It is a static documentation product, not another calculation layer.

## Protected scientific contract

Migration must not incidentally change:

1. additive identity-scale and ratio log-scale computation;
2. CI-midpoint reconstruction, including geometric-midpoint display for ratios;
3. the current 95% CI assumption and estimate-validation role;
4. `2 * Normal.sf(abs(z))` compatibility;
5. `exp(-0.5 * z**2)` normalized Wald relative likelihood;
6. S−2 endpoints at the working-scale estimate plus or minus `2 * SE`;
7. the legacy paired 80% benchmark around the null;
8. the six selected-claim rule keys and tail definitions;
9. Type S as conditional wrong-sign probability among selected claims;
10. Type M as selected expected magnitude divided by true working-scale distance, undefined
    at or near the null;
11. observed exaggeration as a separate retrospective quantity;
12. `SE_design = SE_current / sqrt(information_multiplier)`;
13. strict finite browser JSON, using `null` for undefined quantities;
14. wording that the display is normalized **Wald** relative likelihood, not exact fitted-model
    profile likelihood;
15. repeated-study rather than posterior interpretation for Type S/M; and
16. the non-clinical status of user-entered reference thresholds.

Any formula, tolerance, tail, undefined-value convention, public API, license, or
interpretive change requires a separate explicit decision and validation record.

## Cross-repository dependency contract

1. The core releases a wheel and source distribution with checksums.
2. Every app pins one exact released core version in `pyproject.toml` and `uv.lock`.
3. Browser staging copies the installed locked dependency, not a sibling checkout or
   unpinned branch.
4. A generated browser manifest records app/core versions, source commit, files, and hashes.
5. Core changes are released upstream before downstream adoption.
6. Core upgrade pull requests review the changelog and rerun baseline, app, and browser tests.
7. A required missing primitive is added and released upstream; an app-local formula is a
   release blocker.
8. Public releases never depend on `main` or an editable local path.

The core, distribution, and import names are intentionally distinct:
`wald-inference-core`, `wald-inference`, and `wald_inference`.

## Execution sequence

```text
00 Freeze the integrated baseline
  -> 01 Extract and release wald-inference-core
    -> 02 Rewire the integrated workbench
      -> 03 Create scientific-applet-template
        -> 04 Compatibility curve
        -> 05 Wald likelihood support
        -> 06 Critical effect size
        -> 07 Type S/M calibrator
        -> 08 Precision guardrail planner
          -> 09 Catalog and cross-links
            -> 10 Finalize the integrated workbench role
              -> 11 Independent portfolio validation
```

Milestones 00–03 are serial. Milestones 04–08 may proceed in separate repositories after
the core, adapter, and template are stable, but concurrent changes to
`wald-inference-core` are prohibited. Milestones 09–10 close the portfolio; milestone 11
must use clean clones and a fresh review context.

## Release posture and non-goals

Core and scientific app repositories are treated as reusable, high-consequence research
software. Release requires locked cold installation, unit/property/integration/regression
tests, browser coverage where applicable, scientific validation, CI, versioned artifacts,
citation/license/privacy/maintenance documentation, and independent fresh-context review.

The migration does not itself add exact model likelihood, Bayesian inference, arbitrary
non-Wald intervals, multiparameter likelihoods, validated MCIDs, study-specific sample-size
models, clinical decision support, accounts, persistence, analytics, telemetry, databases,
or server-side computation.

Canonical author and copyright-holder metadata remain approval boundaries documented in
`METADATA_AUDIT.md`.
