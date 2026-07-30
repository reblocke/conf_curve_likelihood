# Changelog

All notable changes to the integrated workbench are documented here.

## [Unreleased]

## [0.2.0] - 2026-07-30

### Changed

- Positioned the existing application as the backward-compatible integrated Wald inference
  workbench and linked the question-based catalog and all five focused tools.
- Upgraded the exact numerical dependency from `wald-inference` v0.1.1 to v0.4.0 without exposing
  new Core fields or changing the legacy `confcurve` request/response contract.
- Replaced raw Pyodide traceback presentation with an authored calculation-error message that
  retains the final exception type and text.
- Added the long-term maintenance policy, routed feature requests to the appropriate focused
  repository, and documented the Core-upgrade review checklist.
- Updated GitHub Actions to current Node 24-compatible action majors.

### Compatibility

- The repository, Pages URL, `confcurve` imports, `compute_curves()` contract, default inputs,
  view modes, warnings/errors, plots, CSV/PNG/caption/reviewer exports, and all 22 B01-B08 frozen
  responses remain protected.
- Core v0.4.0 adds downstream APIs, but this workbench continues to expose only its existing
  adapter contract.

### Dependency provenance

- Core release:
  <https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.0>
- Core release status observed 2026-07-30:
  GitHub prerelease
- Core wheel:
  `wald_inference-0.4.0-py3-none-any.whl`
- Core wheel SHA-256:
  `401a0cc2a182918764149eb03c79672217b647147c494215c83515fd609c7af6`
- Core sdist SHA-256:
  `87b862bc30446695a82e1cb574a98c061a7356069ea2fd1bd5854365c77dc4db`
- Core parity report SHA-256:
  `7619090d95b0767112039c9deec53d284101582692ccd2d8975ace63fb0547bc`
- Core release commit:
  `fd7b24740122bed7ae07769674732c5e56c91277`

### Scientific impact

- No formula, selection rule, numerical tolerance, undefined-value convention, benchmark
  semantics, or scientific interpretation changed. The integrated adapter remains a presentation
  and compatibility layer over the released Core.

## [0.1.1] - 2026-07-29

### Changed

- Moved the authoritative Wald calculations to the exact `wald-inference` v0.1.1 GitHub
  release while retaining `confcurve` as the legacy Python and browser-contract adapter.
- Routed compatibility constants and warning wording through the documented
  `wald_inference.legacy` surface rather than core implementation modules.
- Replaced committed browser Python copies with one ignored, build-time-generated bundle
  containing `wald_inference`, `confcurve`, and a verified package/file manifest.
- Routed local tests, local serving, CI, GitHub Pages, and tagged releases through the same
  `make stage-web` command.

### Compatibility

- Public `confcurve` imports, `compute_curves(payload)`, response keys and ordering,
  warnings, strict-JSON behavior, UI controls and defaults, plots, CSV/PNG exports, caption,
  and reviewer text are intended to be unchanged.
- The 22 frozen B01–B08 request/response cases remain the migration parity authority at
  `rtol=1e-12` and `atol=1e-14`, with declared identity fields compared exactly.

### Dependency provenance

- Core release:
  <https://github.com/reblocke/wald-inference-core/releases/tag/v0.1.1>
- Core release status observed 2026-07-29:
  GitHub prerelease
- Core wheel:
  `wald_inference-0.1.1-py3-none-any.whl`
- Core wheel SHA-256:
  `95bc10d770836544d726362c401032e0640a5a9ec1573f043add7f6bd3a65457`
- Core sdist SHA-256:
  `a650f0041a2082bc1b58413c5ddf59c1e2c0eab48f31c8524943f69369050fb0`
- Core parity report SHA-256:
  `7619090d95b0767112039c9deec53d284101582692ccd2d8975ace63fb0547bc`
- Core release commit:
  `d1ffb0baa46eb8ad27175d58c90e4febc0ac2809`

### Release evidence

- The annotated-tag workflow reruns locked format, lint, staging, golden-parity,
  non-browser tests, the full Chromium suite, and a WebKit smoke test before creating a
  GitHub prerelease.
- Release assets include a deterministic source archive, generated browser-stage manifest,
  and `SHA256SUMS`. The workflow does not publish to PyPI.

### Scientific impact

- This is an implementation-source migration. No formula, selection tail, warning
  threshold, numerical tolerance, undefined-value convention, or public interpretation is
  intentionally changed.

[Unreleased]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.2.0
[0.1.1]: https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.1.1
