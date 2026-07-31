# Changelog

All notable changes to the integrated workbench are documented here.

## [Unreleased]

- Harden CI, Pages, and future releases with reviewed full-SHA Action pins, explicit
  least-privilege permissions, nonpersisted checkout credentials, stable check IDs, and a disabled
  dependency cache in the release-artifact job.
- Require a GitHub-verified signed annotated tag, bind its remote tag object to the event commit,
  require protected-`main` containment before isolated version parsing or repository execution,
  and require exact agreement between the tag and app/citation/changelog versions.
- Install an exact checksummed GitHub CLI before credentialed release commands, require immutable
  releases through a dedicated Administration-read secret, and verify the exact draft assets and
  version-bounded release body before one-time stable publication.
- Add grouped weekly Dependabot proposals with a seven-day cooldown for `uv` and GitHub Actions,
  private vulnerability reporting guidance, contribution policy, scoped issue and pull-request
  templates, and repository-policy regressions. Dependency proposals remain review-only, and the
  updater respects the released scientific `<2.3` NumPy ceiling.
- Pin the development-only security updates pytest 9.0.3, Requests 2.33.0, Pygments 2.20.0,
  urllib3 2.7.0, and idna 3.15 while retaining pytest 9.0.2 solely as frozen fixture provenance;
  no golden file, application runtime, browser stage, Core dependency, or scientific result changes.
- Preserve app version 0.2.5, the exact `wald-inference` v0.4.1 wheel and checksum, all 22 frozen
  B01–B08 cases, `confcurve` compatibility, browser behavior, exports, feature-freeze, and
  scientific/privacy scope.

## [0.2.5] - 2026-07-30

### Changed

- Correct the current
  [`wald-inference` v0.4.1](https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1)
  publication state from GitHub prerelease to stable release after its explicit promotion.
- Reconcile `README.md` and `docs/migration/MIGRATION_LOG.md` with that stable-Core boundary while
  retaining this integrated app's experimental GitHub-prerelease status.
- Preserve all 22 frozen B01-B08 responses, the `docs/SCIENTIFIC_SCOPE.md` and
  `docs/VALIDATION.md` records, and the v0.2.4 numerical, Python, browser-payload, privacy,
  accessibility, UI, and export contracts unchanged.
- Keep the repository, Pages URL, `confcurve` imports, `compute_curves()` contract, default inputs,
  view modes, warnings/errors, plots, and CSV/PNG/caption/reviewer exports backward compatible.
- Continue to route single questions to
  [compatibility-curve](https://reblocke.github.io/compatibility-curve/),
  [wald-likelihood-support](https://reblocke.github.io/wald-likelihood-support/),
  [critical-effect-size](https://reblocke.github.io/critical-effect-size/),
  [type-s-m-calibrator](https://reblocke.github.io/type-s-m-calibrator/), and
  [precision-guardrail-planner](https://reblocke.github.io/precision-guardrail-planner/), under the
  supported-change policy in `docs/MAINTENANCE.md`.
- Treat this as lifecycle-metadata correction only, not clinical validation or scientific revalidation
  beyond the documented frozen tests and independent review.

## [0.2.4] - 2026-07-30

### Changed

- Reconcile `docs/migration/METADATA_AUDIT.md` and `docs/migration/MIGRATION_LOG.md` with the
  completed v0.2.3 annotated tag, release assets, Pages deployment, and independent post-tag
  review. Remove prospective lifecycle statements that became stale after publication.
- Preserve the v0.2.3 numerical, Python, browser-payload, privacy, accessibility, UI, and export
  contracts unchanged. This patch changes documentation and version/policy surfaces only.
- Retain the required `docs/SCIENTIFIC_SCOPE.md` and `docs/VALIDATION.md` records.

### Core and parity

- Pin the exact
  [`wald-inference` v0.4.1](https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1)
  release and wheel SHA-256
  `d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b`.
- Retain all 22 frozen B01-B08 responses at `rtol=1e-12` and `atol=1e-14`, with declared identity
  fields exact.

### Portfolio and maintenance

- Continue to recommend the
  [focused Wald tools catalog](https://reblocke.github.io/wald-inference-tools/) for a single
  question. The focused applications are
  [compatibility-curve](https://reblocke.github.io/compatibility-curve/),
  [wald-likelihood-support](https://reblocke.github.io/wald-likelihood-support/),
  [critical-effect-size](https://reblocke.github.io/critical-effect-size/),
  [type-s-m-calibrator](https://reblocke.github.io/type-s-m-calibrator/), and
  [precision-guardrail-planner](https://reblocke.github.io/precision-guardrail-planner/).
- Retain the supported-change, compatibility, deprecation, and human-gated archival policy in
  [`docs/MAINTENANCE.md`](https://github.com/reblocke/conf_curve_likelihood/blob/v0.2.4/docs/MAINTENANCE.md).
- Keep the repository, Pages URL, `confcurve` imports, `compute_curves()` contract, default inputs,
  view modes, warnings/errors, plots, and CSV/PNG/caption/reviewer exports backward compatible.
- This is software-validation evidence, not clinical validation or scientific revalidation beyond
  the documented frozen tests and independent review.

## [0.2.3] - 2026-07-30

### Added

- Add the canonical `docs/SCIENTIFIC_SCOPE.md` and `docs/VALIDATION.md` records required by the
  cross-repository validation matrix.

### Changed

- Reconcile the migration log and metadata audit with the completed v0.2.1 and v0.2.2 releases.
- Preserve the v0.2.2 numerical, Python, browser-payload, privacy, accessibility, and export
  contracts unchanged.

### Core and parity

- Pin the exact
  [`wald-inference` v0.4.1](https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1)
  release and wheel SHA-256
  `d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b`.
- Retain all 22 frozen B01-B08 responses at `rtol=1e-12` and `atol=1e-14`, with declared identity
  fields exact. This patch changes documentation and version surfaces only.

### Portfolio and maintenance

- Continue to recommend the
  [focused Wald tools catalog](https://reblocke.github.io/wald-inference-tools/) for a single
  question. The focused applications are
  [Compatibility curve](https://reblocke.github.io/compatibility-curve/),
  [Wald likelihood support](https://reblocke.github.io/wald-likelihood-support/),
  [Critical effect size](https://reblocke.github.io/critical-effect-size/),
  [Type S/M calibrator](https://reblocke.github.io/type-s-m-calibrator/), and
  [Precision guardrail planner](https://reblocke.github.io/precision-guardrail-planner/).
- Retain the supported-change, compatibility, deprecation, and human-gated archival policy in
  [`docs/MAINTENANCE.md`](https://github.com/reblocke/conf_curve_likelihood/blob/v0.2.3/docs/MAINTENANCE.md).
- Keep the repository, Pages URL, `confcurve` imports, `compute_curves()` contract, default inputs,
  view modes, warnings/errors, plots, and CSV/PNG/caption/reviewer exports backward compatible.
- This is software-validation evidence, not clinical validation or scientific revalidation beyond
  the documented frozen tests and independent review.

## [0.2.2] - 2026-07-30

### Changed

- Wrap compact observed-panel annotations into bounded lines at mobile widths and rerender them
  when the responsive layout crosses the compact breakpoint.
- Add a rendered-SVG bounding-box regression requiring both observed-panel labels to remain
  inside the plot and 390-pixel viewport.
- Force Chromium E2E dependency loads onto TCP/HTTP2 so isolated test contexts do not inherit
  jsDelivr QUIC transport failures; WebKit and the production browser runtime are unchanged.
- Preserve the feature-frozen numerical, Python, browser-payload, privacy, and export contracts.

## [0.2.1] - 2026-07-30

### Changed

- Upgraded the exact numerical dependency from `wald-inference` v0.4.0 to v0.4.1.
- Retained the feature-frozen `confcurve` Python, browser, and export contracts and did not expose
  additional Core fields or add an app-local formula.

### Dependency provenance

- Core release:
  <https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1>
- Core release commit:
  `f4613177b6dc81d194aa70762152de2bfa86663b`
- Core wheel:
  `wald_inference-0.4.1-py3-none-any.whl`
- Core wheel SHA-256:
  `d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b`
- Core sdist SHA-256:
  `5b30fbc22c416cc724b75d9920157f42886ba185d34b628b4ad4c66691376bbf`
- Core parity report SHA-256:
  `18d020e6a00746646ffed913eb88f1e4b148aa2725872db647823019f1e65dba`

### Scientific impact

- Core v0.4.1 corrects non-monotone threshold precision bracketing, exact pairwise support ratios,
  and strict ratio-scale underflow validation.
- The integrated app's frozen B01–B08 response contract, defaults, views, warnings, plots, and
  exports remain verification gates; no tolerance or scientific definition was widened.

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

[Unreleased]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.2.5...HEAD
[0.2.5]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/reblocke/conf_curve_likelihood/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.2.0
[0.1.1]: https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.1.1
