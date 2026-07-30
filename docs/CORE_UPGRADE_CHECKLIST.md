# Core upgrade checklist

Use this checklist for every `wald-inference` upgrade.

- [ ] Identify the exact release tag, commit, wheel URL, wheel SHA-256, license, and upstream
      scientific-impact notes.
- [ ] Confirm the release artifact is public, immutable, and installable without a sibling checkout.
- [ ] Review added/changed APIs and verify no new field is exposed through `confcurve` implicitly.
- [ ] Update `pyproject.toml`, `uv.lock`, staging constants, runtime expectations, README, `llms.txt`,
      `CITATION.cff`, changelog, decisions/ADR, and migration log.
- [ ] Run `uv sync --locked` and confirm the expected installed Core version and artifact origin.
- [ ] Run `make stage-web`; inspect the package manifest and confirm the exact artifact URL/hash.
- [ ] Run `make golden-check`; B01-B08 must remain within `rtol=1e-12`, `atol=1e-14`, with declared
      identity fields exact.
- [ ] Run public-API, strict-JSON, staging-integrity, non-browser, full Chromium, and WebKit checks.
- [ ] Run `scripts/check_portfolio_links.py` and inspect the deployed input-free URL/privacy path.
- [ ] Verify `git diff --check` and that generated staging leaves tracked state clean.
- [ ] Record any intentional contract change under semantic versioning; unexplained differences
      block release.
- [ ] Retain rollback information for the prior exact pin and last verified app release.
