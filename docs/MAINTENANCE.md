# Maintenance policy

## Status and role

This repository is the maintained, backward-compatible integrated Wald inference workbench. It
keeps observed-data compatibility/relative-support views and assumed-truth repeated-study design
views together for advanced comparison. The focused
[Wald tools catalog](https://reblocke.github.io/wald-inference-tools/) is the preferred entry point
for a single inferential question.

The workbench is feature-frozen by default. Feature-frozen does not mean unsupported: correctness,
security, accessibility, browser compatibility, exact Core upgrades, and documentation remain
maintained.

## Supported changes

- Exact reviewed `wald-inference` Core version upgrades.
- Numerical bug fixes implemented and released in Core first.
- Contract-preserving dependency and security updates.
- Accessibility and browser-compatibility fixes.
- Corrections to documentation, scientific boundaries, versions, and portfolio links.
- Reproducibility, release-provenance, and test improvements that preserve public behavior.

## Normally out of scope

- New inferential paradigms or app-specific formula forks.
- New selection rules introduced only in this workbench.
- Large dashboards, accounts, saved state, backends, telemetry, or input-bearing links.
- Focused-app features that already have a clearer owner elsewhere in the portfolio.
- Removing a protected legacy capability merely because a focused app now exists.

Feature requests should begin at the
[catalog](https://reblocke.github.io/wald-inference-tools/) and be filed in the repository that owns
the requested scientific question.

## Compatibility policy

- The `confcurve` Python surface and browser payload follow semantic versioning.
- The existing repository and Pages URLs remain operational.
- `compute_curves()`, defaults, views, warnings/errors, and exports remain protected by B01-B08 and
  browser contract tests.
- A deprecation is documented for at least one release cycle unless an immediate correctness,
  privacy, or security issue makes that unsafe.
- Core upgrades follow [the Core upgrade checklist](CORE_UPGRADE_CHECKLIST.md) and must pass the
  complete frozen and downstream compatibility suite before release.

## Future archival criteria

Archival or read-only status could be considered only if focused tools replace every legitimate
integrated use case, maintenance resources end, or required browser/runtime dependencies become
unsafe with no supported migration. Archival is a human decision: meeting a criterion does not
automatically archive this repository, remove its site, or break inbound links.

## Reporting

Use the bug template for reproducible contract, browser, accessibility, or documentation defects.
Do not include protected health information or private study data. Use synthetic values sufficient
to reproduce the issue.
