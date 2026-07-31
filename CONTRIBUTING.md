# Contributing

## Repository scope

This repository is the feature-frozen, backward-compatible integrated Wald inference workbench.
It owns the `confcurve` compatibility API, browser payload, orchestration, staging, presentation,
warnings, and exports. Released `wald-inference` is the sole numerical and formula authority. A
single-question feature normally belongs in its focused repository rather than this integrated
workbench.

Preserve the B01–B08 Python/browser/export contract, observed-data versus assumed-truth
conditioning boundary, strict JSON, current defaults, existing Pages URL, and client-side privacy.
Do not add or copy a Wald formula into `confcurve`.

Use the public issue forms only for nonsensitive repository engineering and accessibility reports.
Report vulnerabilities through the private process in [SECURITY.md](SECURITY.md). Never place
credentials, protected health information, patient-level data, unpublished restricted data, or
other sensitive values in an issue, pull request, fixture, screenshot, URL, or workflow log.

## Change process

1. Start from the current `main` branch and make one reviewable change.
2. State assumptions, success criteria, silent-failure risks, and verification before editing.
3. Route missing numerical behavior to a released `wald-inference` version before adopting it here.
4. Keep `src/confcurve/` thin and backward compatible.
5. Regenerate ignored browser Python only with `make stage-web`.
6. Keep the official Core wheel exact-version, URL, and checksum bound.
7. Keep third-party GitHub Actions pinned to reviewed full commit SHAs with version comments.
8. Open a pull request and let `test`, `e2e_chromium`, and `e2e_webkit_smoke` complete before
   merging.

Do not add accounts, a backend, telemetry, persistence, cookies, hidden state, uploads, or
input-bearing URLs. Do not remove a protected integrated capability because a focused app now
exists.

## Verification

Restore the locked environment and run the documented suite:

```bash
uv sync --locked
uv run playwright install chromium webkit
make verify
uv run pytest -q \
  tests/e2e/test_initial_and_inputs.py::test_initial_render_loads_pyodide_and_plots \
  --browser webkit
uv run python scripts/check_portfolio_links.py --live
git diff --check
git status --short
```

A Core or compatibility change additionally requires all 22 B01–B08 cases, public API checks,
strict JSON, staging, clean-clone verification without a sibling Core checkout, and the
[Core upgrade checklist](docs/CORE_UPGRADE_CHECKLIST.md). Document every skipped check or warning.

## Release changes

A release change requires a reviewed pull request and a signed, annotated version tag pointing to
the exact reviewed merge commit. The tag must equal `v` plus the authoritative project version,
and that version needs a nonempty changelog section. The tag workflow:

1. cryptographically verifies the remote tag and binds it to the event commit;
2. requires the verified target to be contained in protected `main` history before isolated
   version parsing or repository execution;
3. reruns formatting, lint, B01–B08, portfolio, non-browser, Chromium, and WebKit gates with
   read-only contents permission;
4. builds and checksums the deterministic source archive and browser manifest before release
   creation;
5. transfers the complete bundle to a narrowly write-enabled publishing job;
6. requires repository release immutability;
7. creates a draft stable release using only the current version's changelog section;
8. downloads and compares every draft asset and the release body; and
9. publishes only the verified draft once as stable.

Before creating the tag, enable immutable releases and configure a repository-scoped
Administration-read token as the `RELEASE_SETTINGS_READ_TOKEN` Actions secret. The publishing job
uses that secret only for the fail-closed settings query; release creation uses the job-scoped
GitHub token.

If a release job fails after draft creation, leave the release as a draft for inspection. Do not
replace assets or move a tag after publication.
