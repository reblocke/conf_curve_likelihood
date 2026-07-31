## Scope

Describe the compatibility, engineering, documentation, governance, or maintenance problem
addressed. If this adds a feature, explain why it belongs in the feature-frozen integrated
workbench rather than its focused repository. Name `wald-inference` when its released numerical
behavior owns the issue.

## Risk and release impact

Describe silent-failure risks, B01–B08 implications, observed-data versus assumed-truth
interpretation, privacy/accessibility effects, generated-stage changes, and release impact.

## Verification

List the exact commands run and their outcomes. Include skipped checks and warnings.

## Checklist

- [ ] No Wald or design-calibration formula was added or copied into `confcurve`.
- [ ] The `confcurve` public API, browser payload, defaults, views, warnings/errors, strict JSON,
      and CSV/PNG/caption/reviewer exports remain backward compatible.
- [ ] All 22 B01–B08 cases pass; an intentional contract change names its authority and migration
      path.
- [ ] Observed-data reconstruction and assumed-truth design calibration remain distinctly
      conditioned and are not described as posterior or clinical guidance.
- [ ] Examples and fixtures are synthetic and contain no credentials, sensitive data, or protected
      health information.
- [ ] No backend, telemetry, persistence, cookies, hidden state, upload, or input-bearing URL was
      added.
- [ ] Generated Python under `web/assets/py/` was produced by `make stage-web`, not edited by hand.
- [ ] Every third-party GitHub Action remains pinned to a full commit SHA with a version comment.
- [ ] The official Core version, URL, and checksum remain synchronized across package metadata,
      lockfile, staging configuration, docs, and tests.
- [ ] `uv sync --locked`, `make verify`, the WebKit smoke, and `make portfolio-links` pass.
- [ ] A Core or staging change passes clean-clone verification without a sibling Core checkout.
- [ ] README, scientific scope, validation, privacy, decisions, maintenance, citation, migration
      records, and changelog were reviewed for synchronization.
