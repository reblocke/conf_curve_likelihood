# ADR 0002: Consume the released core and generate the browser stage

- Status: accepted
- Date: 2026-07-29

## Context

The integrated workbench historically owned both the Wald formulas and the browser-specific
contract. Partitioning the portfolio requires one numerical implementation without changing the
existing `confcurve` imports, `compute_curves()` payloads, UI, exports, or hosted URL. Keeping a
second formula copy in this repository would allow the app and focused tools to drift.

The static Pages app cannot import an installed native Python environment directly. Pyodide still
needs same-origin Python files, but committed copies would duplicate released core source and could
become stale.

## Decision

### Dependency and ownership

Pin the exact `wald-inference` v0.1.1 GitHub release wheel in `pyproject.toml` and `uv.lock`:

- release:
  <https://github.com/reblocke/wald-inference-core/releases/tag/v0.1.1>;
- release status observed 2026-07-29: GitHub prerelease;
- release commit: `d1ffb0baa46eb8ad27175d58c90e4febc0ac2809`;
- wheel:
  <https://github.com/reblocke/wald-inference-core/releases/download/v0.1.1/wald_inference-0.1.1-py3-none-any.whl>;
- wheel SHA-256:
  `95bc10d770836544d726362c401032e0640a5a9ec1573f043add7f6bd3a65457`;
- license: MIT.

`wald_inference` owns effect transformations, Wald reconstruction, compatibility and relative
support, detectability, selection rules, Type S/M, and precision calculations. `confcurve` retains
thin behavior-preserving aliases, browser request/response types, app defaults, payload assembly,
display-range choices, warning composition, and strict-JSON conversion. A missing numerical
primitive is implemented and released upstream before it is adopted here.
Compatibility constants and warning wording are consumed through the documented
`wald_inference.legacy` surface rather than implementation modules.

### Browser staging

Use `make stage-web` as the only supported staging entrypoint for local tests, E2E tests, local
serving, CI, tagged releases, and GitHub Pages. The command reads the locked installed
`wald_inference` package and local `confcurve` adapter, atomically replaces the ignored
`web/assets/py/` directory, and writes `web/assets/py/manifest.json`.

The manifest records its schema version, app/core package names and versions, the 40-character
source commit, an ordered file inventory with path, byte count, and lowercase SHA-256 digest, and
an aggregate `bundle_sha256`. Browser startup validates the schema and package metadata, rejects
invalid or duplicate paths, fetches files without cache reuse and with digest-qualified URLs,
checks every file and aggregate digest with Web Crypto, and imports neither package unless the
complete bundle passes.

Generated stage files are not source and are never hand-edited or committed. Atomic replacement
means a removed package file cannot survive as stale output. A clean checkout stages solely from
its locked environment and local adapter; it does not inspect or require a sibling core checkout.

### Compatibility and upgrades

App v0.1.1 preserves the frozen pre-split Python and browser behavior. Public request/response
fields, key ordering, errors, warnings, strict JSON, default controls, plots, exports, caption, and
reviewer text remain governed by the milestone-00 corpus and browser tests.

For a future core upgrade:

1. review the upstream changelog, scientific-impact notes, release artifacts, and checksums;
2. update the exact released artifact and regenerate `uv.lock`;
3. keep `confcurve` wrappers free of formula bodies;
4. run legacy API, frozen B01–B08, strict-JSON, staging-integrity, Chromium, and WebKit checks;
5. inspect the generated manifest and confirm staging leaves tracked Git state clean; and
6. record the adopted core release and checksum in the changelog and migration log.

Rollback restores the prior `pyproject.toml` and `uv.lock` pin, reruns `make stage-web`, and
redeploys the last verified app release. Generated Python is never used as a rollback source.

## Consequences

- Local Python, browser execution, CI, and Pages consume one exact core release.
- The integrated URL and app-specific contract remain local and backward compatible.
- Staging becomes a required build step, but `make test`, `make e2e`, `make serve`, and
  `make verify` invoke it automatically.
- A core release must remain downloadable when creating a new environment; an already populated
  trusted cache may satisfy the same locked artifact without network access.
- Formula changes require an upstream release and cross-repository review.

## Alternatives Considered

- **Keep formulas in `confcurve`:** rejected because it creates a production fork.
- **Commit staged core and adapter files:** rejected because generated copies can drift and obscure
  their release provenance.
- **Use a sibling checkout or editable path:** rejected because clean clones and Pages would depend
  on undeclared local state.
- **Pin `main` or an unversioned Git reference:** rejected because it is not an immutable released
  artifact.
- **Move the browser contract into the core:** rejected because DOM/payload/export choices are app
  responsibilities rather than numerical primitives.

## Validation

The migration gate is:

```bash
uv sync --locked
make stage-web
make verify
uv run python scripts/generate_golden_baseline.py --check
uv run python scripts/compare_golden_baseline.py
git diff --check
git status --short
```

CI and Pages run `make stage-web` from a clean GitHub checkout and fail if generation changes
tracked state. The tag workflow repeats locked non-browser, golden, staging, full-Chromium, and
WebKit-smoke checks before publishing a deterministic source archive, the generated browser
manifest, and checksums to a GitHub prerelease. It does not publish to PyPI.

## 2026-07-30 upgrade record

App v0.2.0 applies the upgrade procedure above and adopts the exact `wald-inference` v0.4.0
release without changing the legacy adapter contract:

- release:
  <https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.0>;
- release commit: `fd7b24740122bed7ae07769674732c5e56c91277`;
- wheel:
  <https://github.com/reblocke/wald-inference-core/releases/download/v0.4.0/wald_inference-0.4.0-py3-none-any.whl>;
- wheel SHA-256:
  `401a0cc2a182918764149eb03c79672217b647147c494215c83515fd609c7af6`;
- license: MIT.

The newer Core APIs remain available to focused downstream tools but are not automatically exposed
through `confcurve`. B01-B08, the public Python surface, strict JSON, browser contract, and exports
remain the compatibility gate.
