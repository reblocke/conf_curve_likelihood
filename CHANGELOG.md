# Changelog

All notable changes to the integrated workbench are documented here.

## [Unreleased]

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

[Unreleased]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.1.1
