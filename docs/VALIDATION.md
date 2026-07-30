# Validation

## What validation establishes

Passing this repository's gates shows that the integrated adapter preserves its frozen numerical,
Python, browser, and export contracts while delegating statistical calculations to the pinned
Core release. It does not establish that a Wald approximation is appropriate for a particular
study, validate a user-supplied threshold, or certify clinical use.

The validation strategy separates:

1. frozen B01-B08 numerical and contract parity;
2. Core formula ownership and exact dependency provenance;
3. deterministic browser staging and release traceability;
4. browser behavior, accessibility, privacy, and exports; and
5. deployed portfolio-link and runtime-version checks.

## Frozen baseline authority

The immutable baseline release is
[`pre-split-baseline-2026-07-29`](https://github.com/reblocke/conf_curve_likelihood/releases/tag/pre-split-baseline-2026-07-29).
Its manifest identifies behavior-source commit
`830756ecb11b4e8161f8dfe1fc75afc346ef4467`. The 22 stored B01-B08 cases preserve:

- the `confcurve` public import surface;
- `compute_curves()` request/response schema, ordering, warnings, and errors;
- additive and ratio-scale observed reconstructions;
- display-only range behavior;
- forward design calibration and threshold rules;
- inverse-precision targets;
- undefined, invalid, infeasible, and extreme finite-value behavior;
- strict JSON;
- default browser inputs and view modes; and
- CSV, PNG, caption, and reviewer-text contracts.

The fixture manifest SHA-256 is
`f54bb2d8311788c07adcf23fc9f038e35702449e4a77a474abea9411246cabcc`; the complete
fixture-set SHA-256 is
`81c341b39e711caffc85a444f0c1e4bc1e2d00633474c82e720afeb60def3c4d`.

Local scientific comparisons use `rtol=1e-12` and `atol=1e-14`, with declared identity fields
compared exactly. Browser cross-engine comparisons may use `rtol=1e-10` and `atol=1e-12`.
Tolerances may not be widened merely to make a failing result pass.

## Scientific ownership and dependency checks

Source-policy and parity tests require statistical primitives to resolve through the released
`wald-inference` package. The integrated repository retains compatibility-shaped adapters and
presentation logic but must not add a second production implementation of a Core formula or
selection rule.

The exact Core 0.4.1 wheel URL is bound across `pyproject.toml`, `uv.lock`, staging metadata,
installed direct-URL metadata, documentation, and tests. Its SHA-256 is bound in dependency
metadata, the lockfile, staging constants, documentation, and tests; installed file identity is
also checked against the wheel `RECORD`. `make stage-web` copies the installed `wald_inference` and
`confcurve` packages into an ignored build directory, records every file and digest, and writes an
aggregate bundle digest plus the source commit. The browser verifies that manifest before
importing either package.

## Numerical and contract gates

The non-browser suite covers:

- all 22 frozen B01-B08 cases and exact JSON serialization;
- public API compatibility and response ordering;
- additive and ratio reconstruction, support, selection, Type S/M, and precision paths;
- undefined and infeasible results represented as `null` or explicit no-solution status;
- extreme finite-value clipping and error behavior;
- no out-of-contract fields exposed by a Core upgrade;
- deterministic staging, stale-file removal, and manifest tamper rejection;
- release metadata, workflow, repository-policy, and portfolio-link contracts; and
- source-format, lint, and release-workflow clean-tree gates.

The parity generator and comparator are independently callable so the stored baseline cannot be
silently regenerated during verification.

## Browser, privacy, and accessibility gates

Chromium end-to-end tests cover runtime initialization, default and edited calculations, every
view, design controls, error recovery, text/table/plot agreement, responsive layouts, mobile
annotation containment, keyboard operation, and all exports. WebKit smoke covers initial runtime
and rendered calculation behavior.

Static and dynamic policy tests require:

- no backend, telemetry, analytics, cookies, service worker, or persistent storage;
- no input value in URLs or network requests;
- only version-pinned static CDN/package requests;
- labels, visible focus, keyboard operation, and status and error live regions;
- a text/table alternative and plot description;
- documented CSV columns and nonempty PNG dimensions; and
- input-free related-tool links.

## Commands

Run the documented release gates literally:

```bash
uv sync --locked
uv run playwright install chromium webkit
make verify
uv run pytest -q \
  tests/e2e/test_initial_and_inputs.py::test_initial_render_loads_pyodide_and_plots \
  --browser webkit
uv run python scripts/generate_golden_baseline.py --check
uv run python scripts/compare_golden_baseline.py
uv run python scripts/check_portfolio_links.py
git diff --check
git status --short
```

`make verify` stages the browser packages, checks formatting and lint, runs baseline and
non-browser tests, and runs the full Chromium suite. The WebKit smoke and explicit Git
diff/status checks are separate commands locally and mandatory steps in the release workflow.
Generated ignored build/test directories may exist afterward; tracked source must remain clean.

## Release evidence

Each release record should identify:

- annotated tag object and peeled commit;
- app, Core, Python, Pyodide, NumPy, SciPy, Plotly, and browser versions;
- Core artifact URL and digest;
- staged package manifest and bundle digests;
- local and GitHub CI/browser results;
- Pages workflow and deployed manifest source commit;
- release assets and published checksums;
- frozen numerical maximum absolute and relative differences; and
- any evidence limitations or unresolved findings.

The independent portfolio audit and its machine-readable status live in the
[`wald-inference-tools`](https://github.com/reblocke/wald-inference-tools) catalog repository.
Only that external evidence can change the portfolio status; a successful workbench release does
not establish or self-certify the portfolio verdict.

## Known validation boundary

The software tests and independent audit address implementation correctness, frozen parity,
release traceability, accessibility, privacy, and documentation. They do not validate the
appropriateness of a source study's model, the correctness of a reported interval, the scientific
meaning of a user-entered threshold, or any clinical decision.
