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

## Dependency and automation updates

Review Pyodide, Plotly, Python, NumPy, SciPy, uv, Ruff, pytest, Hypothesis, Playwright, GitHub
Actions, and especially `wald-inference` deliberately. Dependabot groups weekly `uv` and GitHub
Actions updates after a seven-day cooldown for review; it does not authorize automatic merging.
Keep every third-party Action pinned to a reviewed full commit SHA with its version in a comment.
The updater ignores NumPy versions at or above 2.3 because the released Core/scientific
compatibility contract requires the existing `<2.3` ceiling; changing that ceiling requires a
reviewed compatibility upgrade, not an unresolvable automated proposal.

For a Core update, follow [the Core upgrade checklist](CORE_UPGRADE_CHECKLIST.md), update the exact
wheel version, URL, and SHA-256 together, regenerate the lock and browser stage, and rerun the
complete B01–B08, compatibility, strict-JSON, Chromium, WebKit, portfolio, and clean-clone gates.
Do not replace Core with a local formula, copied module, path dependency, floating version, mutable
branch artifact, or sibling checkout.

## Release

Use a reviewed pull request. After the exact merge commit is verified, create a signed, annotated
semantic-version tag. The release workflow verifies the remote tag object and signature, binds the
tag target to the event commit, and requires that commit to be contained in protected `main`
history before isolated project-version parsing or repository execution. It reruns formatting,
lint, B01–B08, live portfolio links, non-browser tests, Chromium, and WebKit under read-only
contents permission. The release-artifact job disables shared dependency caching and builds the
deterministic source archive, browser-stage manifest, and SHA-256 checksums before a release
exists.

A separate job with narrowly scoped contents-write permission uses an exact checksummed GitHub
CLI, requires repository release immutability through the `RELEASE_SETTINGS_READ_TOKEN` Actions
secret, and creates a draft stable release containing every expected asset and only the tagged
version's nonempty changelog section. It re-downloads and compares the exact draft assets and
release body, then publishes the verified draft once as stable.

If the workflow fails after draft creation, retain the draft for inspection. Repair the workflow
and create a new tag only after the failure is understood; never move a published tag or replace a
published asset. Complete CI, GitHub Pages, hosted runtime/version, browser, export, privacy, and
portfolio-level validation before creating the tag.

Repository settings must retain read-only default workflow permissions, protect `main` and `v*`
tags, enable private vulnerability reporting and Dependabot security updates, and enable immutable
releases before the next tag is created. Store a repository-scoped Administration-read token as
the `RELEASE_SETTINGS_READ_TOKEN` Actions secret so the workflow can fail closed before
publication. The job-scoped GitHub token, not that settings-read secret, creates the release.

## Future archival criteria

Archival or read-only status could be considered only if focused tools replace every legitimate
integrated use case, maintenance resources end, or required browser/runtime dependencies become
unsafe with no supported migration. Archival is a human decision: meeting a criterion does not
automatically archive this repository, remove its site, or break inbound links.

## Reporting

Use the scoped issue forms for reproducible contract, browser, accessibility, or documentation
defects. Do not include protected health information, private study data, credentials, restricted
materials, or vulnerability details. Use synthetic values sufficient to reproduce a nonsensitive
issue and the private process in `SECURITY.md` for vulnerabilities.
