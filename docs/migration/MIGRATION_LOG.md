# Portfolio Migration Log

## Update rules

- Add one entry for each milestone and append dated corrections rather than silently
  rewriting completed evidence.
- Distinguish planned, implemented, verified, merged, tagged, released, and deployed states.
- Record only commands and external actions that were actually observed.
- Identify the exact source and target SHAs, expected PR head, tags, artifact hashes, and
  released core version.
- State whether outputs changed intentionally. A migration-only milestone should say
  “none,” not leave the field blank.
- Carry unresolved scientific, API, identity, license, and release decisions forward until
  an authoritative resolution is recorded.

## Milestone 00 — Freeze and characterize the integrated baseline

> Historical entry retained as recorded; the dated evidence corrections at the end of this
> milestone supersede the qualified statements they identify.

| Field | Status |
|---|---|
| Date opened/completed | 2026-07-29 |
| Source repository | `reblocke/conf_curve_likelihood` |
| Target repository | `reblocke/conf_curve_likelihood` |
| Source branch/SHA | `main` at `830756ecb11b4e8161f8dfe1fc75afc346ef4467` |
| Working branch | `codex/mig-00-freeze-baseline` |
| Audited-versus-actual comparison | Initially identical; final source adds only approved PRs #13 and #14 |
| Pull request | [#11](https://github.com/reblocke/conf_curve_likelihood/pull/11), merged with expected head `d6c709d9f7bcf09a156295e09025c8f8bfd3d923` |
| Baseline merge SHA | `5fd501dd947d9b951d736014cfc2b310efa5e7b0` |
| Baseline tag | [`pre-split-baseline-2026-07-29`](https://github.com/reblocke/conf_curve_likelihood/releases/tag/pre-split-baseline-2026-07-29), annotated target verified as the baseline merge SHA |
| Core version | Not applicable; numerical code is still integrated in `confcurve` |
| Validation status | Complete; local suite and all six final GitHub CI jobs passed |
| Intended production behavior changes | One separately approved finite-range safety correction in PR #14; ordinary behavior unchanged |
| Fixture manifest/hash | Manifest `f54bb2d8311788c07adcf23fc9f038e35702449e4a77a474abea9411246cabcc`; fixture set `81c341b39e711caffc85a444f0c1e4bc1e2d00633474c82e720afeb60def3c4d` |
| Release notes/release URL | [Pre-split integrated baseline (2026-07-29)](https://github.com/reblocke/conf_curve_likelihood/releases/tag/pre-split-baseline-2026-07-29) |

### Work recorded

- Selected the audited source, then advanced the behavior-freeze source only for the
  explicitly approved metadata and strict-JSON corrections in PRs #13 and #14.
- Added repository-local migration documentation and metadata inventory.
- Recorded the target architecture without moving formulas; the only production change is
  the separately approved finite-range safety correction.
- Defined 22 B01–B08 cases, including B08e for the rejected unrepresentable design distance,
  plus machine-readable contract/export schemas, an exact effect
  registry snapshot, and deterministic comparison tooling.
- Added exact downloaded CSV-header and PNG-dimension browser gates.

### Validation evidence

- `make verify` passed after the initial hardened corpus and browser export checks.
- The current post-review corpus passed its 22-test focused integration suite, generator
  check, comparator, Ruff format/lint checks, and `git diff --check`.
- PR #14 passed its full local suite, focused Chromium/WebKit regression, independent
  numerical review, and all GitHub CI jobs.
- Final corpus generation/check and comparison passed for 22 cases at `rtol=1e-12`,
  `atol=1e-14`.
- Final `make verify` passed with 157 non-E2E and 43 Chromium E2E tests; `uv sync --locked`,
  Chromium/WebKit installation, Ruff, and `git diff --check` also passed.
- Final PR head passed two unit jobs, two 43-test Chromium jobs, and two WebKit smoke jobs
  before expected-head squash merge.

### Resolved decisions and remaining risks

- Canonical public identity is `Brian Locke`; the MIT copyright line is
  `Copyright (c) 2026 Brian Locke` (PR #13).
- [Issue #12](https://github.com/reblocke/conf_curve_likelihood/issues/12) was explicitly
  approved and implemented in PR #14. B08e merged in PR #11, after which issue #12 was
  closed.
- The fixtures are generated characterization outputs rather than independent scientific
  reference truth. Extraction and downstream repositories must retain independent unit,
  property, boundary, and clean-artifact validation in addition to parity.

### Completion evidence

- Reviewed PR head: `d6c709d9f7bcf09a156295e09025c8f8bfd3d923`.
- Merged commit: `5fd501dd947d9b951d736014cfc2b310efa5e7b0`.
- Corpus: 22 cases and 50 deterministic JSON artifacts.
- Comparator: `rtol=1e-12`, `atol=1e-14`, plus declared exact paths.
- Manifest SHA-256:
  `f54bb2d8311788c07adcf23fc9f038e35702449e4a77a474abea9411246cabcc`.
- Fixture-set SHA-256:
  `81c341b39e711caffc85a444f0c1e4bc1e2d00633474c82e720afeb60def3c4d`.
- Annotated tag object: `58855d85227864efb30b7e66a79c28cb13103608`; peeled target:
  `5fd501dd947d9b951d736014cfc2b310efa5e7b0`.
- Release:
  `https://github.com/reblocke/conf_curve_likelihood/releases/tag/pre-split-baseline-2026-07-29`.
- No production formula change was introduced by PR #11. The only intentional difference
  from the audited source remains the separately approved PR #14 boundary correction.

### Evidence corrections — 2026-07-30

These corrections supersede the affected wording above without erasing the original milestone
record:

- Issue #12 explicitly said its creation was not approval. Authorization was later supplied in the
  migration task outside GitHub; PR #14 then implemented the strict-JSON boundary correction.
- The PR #13 metadata choice was likewise not publicly approved on GitHub. The migration task
  owner later confirmed the exact author identity as `Brian Locke` and the license as MIT.
- PR #14 is the only intentional production-behavior difference. PR #13 metadata and PR #11
  documentation/testing surfaces were also intentional non-production differences.
- GitHub Actions independently evidences the passing CI jobs. The local-suite and numerical-review
  statements are implementation observations that are not independently recoverable from the
  public Actions record.

## Milestone 02 — Rewire the integrated workbench to the released core

> Historical entry retained as recorded; the dated evidence corrections at the end of this
> milestone supersede the qualified statements they identify.

| Field | Status |
|---|---|
| Date opened/completed | Opened and completed 2026-07-29 |
| Source repository/SHA | `reblocke/conf_curve_likelihood` at `45c29e8f57ef793f40688e5352249c73f1001295` |
| Target repository/SHA | Candidate `d83d066411d2baf0281fa5c68e25b958d10fefd2`; merged `201f4a57b337ab7a82e85d08aa458c775a5825da` |
| Branch | `codex/mig-02-rewire-core` |
| Pull request | [#16](https://github.com/reblocke/conf_curve_likelihood/pull/16), merged at the exact candidate head |
| Tag/release | Annotated `v0.1.1`; [prerelease](https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.1.1) |
| Core version | Exact `wald-inference` v0.1.1 release |
| Core artifact | [`wald_inference-0.1.1-py3-none-any.whl`](https://github.com/reblocke/wald-inference-core/releases/download/v0.1.1/wald_inference-0.1.1-py3-none-any.whl) |
| Core release commit | `d1ffb0baa46eb8ad27175d58c90e4febc0ac2809` |
| Validation status | Local, clean-clone, PR, main, release, Pages, and hosted-smoke gates passed |
| Intended behavior changes | None; formula ownership and staging mechanism only |
| Artifact/manifest hashes | Core wheel `95bc10d770836544d726362c401032e0640a5a9ec1573f043add7f6bd3a65457`; release manifest `80d205c692182c68131cf23ebbb8ff416d1a2aac893f61aaeb056f53729f0829`; source archive `ac9c9c7246573e0e86e0a4ecb6e82bd0af5ae2c051e28941e0cf90f8df368f44` |

### Work recorded

- Convert `confcurve` formula modules into compatibility adapters over the released core while
  retaining the frozen Python exports and browser contract.
- Pin the exact released wheel in project metadata and `uv.lock`; no branch, sibling checkout, or
  editable path is a runtime authority.
- Replace tracked generated Python with an ignored, atomically generated
  `web/assets/py/` bundle containing both packages and `manifest.json`.
- Route local tests, local serving, CI, Pages, and tagged releases through `make stage-web`.
- Publish app v0.1.1 as an annotated, immutable prerelease after exact-head review and CI.

### Validation evidence

- `uv sync --locked` resolved and checked the locked environment successfully.
- `make stage-web` generated 7 app files and 14 core files plus the manifest.
- `make golden-check` passed all 22 frozen cases at `rtol=1e-12`, `atol=1e-14`.
- `uv run pytest -q -m "not e2e"` passed the complete 196-test non-browser suite.
- The focused public-API, staging-provenance, release-policy, core, design, and property command
  passed all 128 selected tests.
- All three workflow files parsed as YAML; the five release-policy tests passed; changelog-note
  extraction produced a nonempty 44-line body without link-definition residue; and two
  independently compressed `git archive` outputs compared byte-for-byte identical.
- A fresh download of the pinned wheel matched SHA-256
  `95bc10d770836544d726362c401032e0640a5a9ec1573f043add7f6bd3a65457`; its metadata reports
  `wald-inference` 0.1.1 under MIT. The release sdist and parity-report SHA-256 values are
  `a650f0041a2082bc1b58413c5ddf59c1e2c0eab48f31c8524943f69369050fb0` and
  `7619090d95b0767112039c9deec53d284101582692ccd2d8975ace63fb0547bc`.
- `make fmt-check` passed for all 31 Python files, `make lint` passed, and `git diff --check`
  reported no whitespace errors. Two consecutive stages produced byte-identical manifests
  for the current checkout.
- Full local browser verification passed 48 Chromium tests and the WebKit initial-render smoke.
- A disposable clone at candidate `d83d066411d2baf0281fa5c68e25b958d10fefd2`, in a parent
  containing no sibling core checkout and with `PYTHONPATH` unset, passed locked sync,
  deterministic staging, format, lint, all 22 golden cases, and all 196 non-browser tests.
  The imported core resolved inside that clone's `.venv`, and `direct_url.json` identified the
  exact v0.1.1 release wheel.
- Both push and pull-request CI runs passed `test`, full Chromium, and WebKit smoke at the exact
  candidate head:
  [run 30514211604](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30514211604)
  and
  [run 30514221666](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30514221666).
- Main-branch [CI](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30514706107),
  [Pages](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30514706117), and the
  browser-gated [release workflow](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30514716144)
  all passed at merge commit `201f4a57b337ab7a82e85d08aa458c775a5825da`.
- The annotated `v0.1.1` tag peels to the merge commit. Downloaded release assets passed the
  published `SHA256SUMS`; the release manifest records app/core 0.1.1, 7/14 files, source commit
  `201f4a57b337ab7a82e85d08aa458c775a5825da`, and bundle SHA-256
  `784a3a5cd44ee5d3629945c9d93df63b8df164f3c3f5e374de3598a86a545313`.
- Hosted smoke at
  [reblocke.github.io/conf_curve_likelihood](https://reblocke.github.io/conf_curve_likelihood/)
  verified the 0.1.1/0.1.1 footer, default ratio reconstruction, the B01 additive
  reconstruction, validation-error recovery, unchanged input-free URL, and enabled local export
  controls. Release-gated E2E separately verifies CSV, PNG, and caption contents.
- Frozen authority remains 22 B01–B08 cases at `rtol=1e-12`, `atol=1e-14`, with manifest SHA-256
  `f54bb2d8311788c07adcf23fc9f038e35702449e4a77a474abea9411246cabcc` and fixture-set SHA-256
  `81c341b39e711caffc85a444f0c1e4bc1e2d00633474c82e720afeb60def3c4d`.
- Required candidate commands and ownership boundaries are recorded in
  [ADR 0002](../adr/0002-released-core-and-generated-browser-stage.md).
- GitHub Actions clean checkouts provide the ongoing no-sibling test: locked install fetches the
  released artifact, `make stage-web` generates the ignored bundle, and the jobs fail if tracked
  state changes.
- No scientific, golden, strict-JSON, Python-API, browser-contract, or export difference was
  accepted in this migration.

### Unresolved decisions and remaining risks

- At this milestone, Core and app releases intentionally remained GitHub prereleases until the
  independent portfolio-validation milestone decided whether to promote them.
- Core v0.4.1 was subsequently promoted to a stable GitHub release on 2026-07-30. Focused and
  integrated apps remain explicitly experimental prereleases.
- Invalid-input display retains the frozen pre-split behavior, including Pyodide traceback text.
  The worker recovers when corrected. Safe-message presentation is deferred to the integrated
  workbench finalization milestone rather than being introduced as an unapproved migration
  difference.

### Evidence corrections — 2026-07-30

These corrections supersede the affected wording above:

- GitHub reports the v0.1.1 release as annotated and prerelease, but not immutable
  (`immutable=false`).
- The exact release-workflow `awk` at candidate `d83d066411d2baf0281fa5c68e25b958d10fefd2`
  produces 51 lines; the live release body has 52 lines including its trailing blank.
- Push run 30514211604 tested exact candidate
  `d83d066411d2baf0281fa5c68e25b958d10fefd2`. Pull-request run 30514221666 tested GitHub's
  synthetic merge `639847847a2099a3ab384c0ee23aa4e596798cb0`, which merged that candidate into
  then-current base `45c29e8f57ef793f40688e5352249c73f1001295`.
- The local-suite, disposable-clone, and hosted-smoke execution claims are implementation
  observations that are not independently recoverable from the public GitHub record. Publicly
  recoverable evidence covers the cited CI, Pages, and release runs plus published artifacts and
  checksums.
- “After exact-head review” refers to candidate-head verification and expected-head merge
  protection; no separate GitHub review or comment independently substantiates that review claim.
- The verified version footer was an intentional presentation change. No numerical, Python API,
  browser-payload, or export-contract change was intended.
- The historical no-difference assurance is limited to the named, tested scientific, golden,
  strict-JSON, Python-API, browser-payload, and export contracts. It does not exclude the recorded
  presentation, staging, dependency, or workflow changes.
- The v0.1.1 app had no Web Worker; the browser runtime recovered after corrected input.

## Milestone 10 — Finalize the integrated workbench role

| Field | Status |
|---|---|
| Date opened/completed | Opened 2026-07-30; implementation merged, prerelease pending at this evidence commit |
| Source repository/SHA | `reblocke/conf_curve_likelihood` / `92db9ad6d68300f029c9a099286b7414a53dc32b` |
| Target repository/SHA | Candidate `2f4f8aae9285e59daf545c12d9c035432c084e87`; merged `5d0ac9ff7b35df2388614a5d9ff2bec513c957fe` |
| Branch | `codex/mig-10-finalize-workbench` |
| Pull request | [#19](https://github.com/reblocke/conf_curve_likelihood/pull/19), merged at the exact candidate head |
| Tag/release | Planned annotated `v0.2.0` prerelease; no tag or release exists at this pre-tag evidence commit |
| Core version | Exact `wald-inference` v0.4.0 release |
| Core artifact | [`wald_inference-0.4.0-py3-none-any.whl`](https://github.com/reblocke/wald-inference-core/releases/download/v0.4.0/wald_inference-0.4.0-py3-none-any.whl) |
| Validation status | Release candidate pending independent portfolio validation |
| Intended behavior changes | Integrated-workbench positioning, portfolio navigation, authored browser-error presentation, maintenance/routing policy, and workflow runtimes; no formula, Python API, browser-payload, or export-contract change |
| Artifact/manifest hashes | Core wheel `401a0cc2a182918764149eb03c79672217b647147c494215c83515fd609c7af6`; deployed browser bundle `13af1bef8091181753ad1c018283435c10d8b9801b3ecb049db1014c38678df5`; source/release checksums pending the tag workflow |

### Work recorded

- Preserve the repository/package/Pages identity and every protected Python, browser, default,
  view, warning/error, and export contract.
- Recommend the focused catalog for a single question while retaining every advanced integrated
  panel.
- Adopt Core v0.4.0 only through its exact released wheel and keep all newly added Core APIs
  outside the legacy browser response.
- Add the feature-freeze, compatibility, deprecation, request-routing, upgrade, and future archival
  policies.
- Replace raw Pyodide traceback display with a stable authored error while retaining the final
  exception type/text and recovery behavior.
- Move CI, Pages, and release workflows to current Node 24-compatible action majors.
- Update the public repository description/homepage and close
  [issue #5](https://github.com/reblocke/conf_curve_likelihood/issues/5) after the upgraded
  workflows passed on `main`.

### Validation authority

- The unchanged 22-case B01-B08 corpus remains authoritative at `rtol=1e-12`, `atol=1e-14`, with
  declared identity fields exact.
- Local final verification passed the 22 B01-B08 cases, 205 non-browser tests, all 48 Chromium
  tests, WebKit initial-render smoke, strict JSON, public API, deterministic staging,
  portfolio-link, duplicate/stale-link, clean-tree, and export/error-recovery gates.
- Push CI tested exact candidate `2f4f8aae9285e59daf545c12d9c035432c084e87`; pull-request
  CI tested GitHub's synthetic merge `67466f09e6eafac5f0154e58a5c016246d3a9b91`, which merged
  that candidate into then-current base `92db9ad6d68300f029c9a099286b7414a53dc32b`. Both passed:
  [run 30536727262](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30536727262)
  and
  [run 30536744401](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30536744401).
- Post-merge [main CI](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30537447640)
  and [Pages](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30537447689)
  passed at merge commit `5d0ac9ff7b35df2388614a5d9ff2bec513c957fe`.
- Hosted Chromium verified app/Core versions, the exact ten-link footer, a rendered plot, input-free
  URLs, zero input-triggered network requests, and no cookies, local/session storage, IndexedDB,
  service worker, or mobile overflow. The live-link check reached all ten public targets.

### Unresolved decisions and remaining risks

- Scientific and portfolio validation status remains `release-candidate` until Milestone 11.
- Future archival remains an explicit human decision; this milestone does not archive or redirect
  the repository.

## Milestone 11 corrective release — Core v0.4.1 adoption

| Field | Status |
|---|---|
| Date opened/completed | Completed 2026-07-30 |
| Source repository/SHA | `reblocke/conf_curve_likelihood` / `5fbf609df072100905d2a86ecbd55b286b5fa090` |
| Target repository/SHA | `reblocke/conf_curve_likelihood` / `daae30681d1ac8c7c13a7afc085b13e0b56d23d2` |
| Branch | `codex/mig-11-core-v041` |
| Pull request | [#21](https://github.com/reblocke/conf_curve_likelihood/pull/21) |
| Tag/release | Annotated `v0.2.1`; its failed release workflow was superseded by v0.2.2 |
| Core version | Exact `wald-inference` v0.4.1 release |
| Core artifact | [`wald_inference-0.4.1-py3-none-any.whl`](https://github.com/reblocke/wald-inference-core/releases/download/v0.4.1/wald_inference-0.4.1-py3-none-any.whl) |
| Validation status | Superseded by v0.2.2 before the independent portfolio-validation rerun |
| Intended behavior changes | Replace invalid Core v0.4.0 edge behavior while retaining the feature-frozen integrated contract |
| Artifact/manifest hashes | Core wheel `d7272023f65088729d3ff997cab7cac57b84f22ac6108244ec2170434557d99b`; no v0.2.1 release assets were published after its release workflow failed |

### Work recorded

- Pin the exact Core v0.4.1 release in Python, browser staging, documentation, and public markers.
- Keep all numerical formulas in Core and expose no new response fields.
- Preserve the 22-case B01-B08 baseline and every public compatibility gate.

### Validation evidence

- Core v0.4.1 release checksums and a clean wheel install passed before adoption.
- Full local verification and main CI/Pages passed. The v0.2.1 release workflow failed during
  browser transport setup; v0.2.2 corrected the test transport without changing production
  numerical behavior and became the audited artifact.

### Unresolved decisions and remaining risks

- None specific to this superseded release.

## Milestone 11 corrective release — responsive browser evidence

| Field | Status |
|---|---|
| Date opened/completed | Completed 2026-07-30 |
| Source repository/SHA | `reblocke/conf_curve_likelihood` / `daae30681d1ac8c7c13a7afc085b13e0b56d23d2` |
| Target repository/SHA | `reblocke/conf_curve_likelihood` / `78d189ac03ec223a69778843497d27c70a8720c2` |
| Branch | `codex/mig-11-mobile-plot-readability` |
| Pull request | [#22](https://github.com/reblocke/conf_curve_likelihood/pull/22) |
| Tag/release | [v0.2.2 prerelease](https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.2.2) |
| Core version | Exact `wald-inference` v0.4.1 release |
| Validation status | Independently audited release candidate |
| Intended behavior changes | Keep observed-panel annotations inside compact plots and make isolated Chromium dependency loading deterministic |
| Artifact/manifest hashes | Source archive `2b3c752dd1c6e25fb81bb2c495fdec23c8d724a7db219575e28a5ce78e07f5f1`; stage manifest `b81f7b5781d77ae0ed1f95b513d6f7f3f27ac853ae2b552d2ea5aebb4210e073`; checksum file `4c64b4ad316fa58842a8a790b229251ea429bfb51ff5efca38ef7b7bb9bb5dd3` |

### Work recorded

- Wrap compact observed-panel annotations and rerender when the layout crosses the compact
  breakpoint.
- Add numerical rendered-SVG containment regressions at a 390-pixel viewport.
- Keep production CDN/runtime behavior unchanged while forcing isolated Chromium test requests
  onto the reliable transport path.

### Validation evidence

- Main CI [run 30555099468](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30555099468),
  Pages [run 30555099460](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30555099460),
  and release [run 30555863567](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30555863567)
  passed at the release commit.
- The published checksum file verifies all three release assets.

### Unresolved decisions and remaining risks

- Portfolio validation remained evidence-limited pending completion of Milestone 11.

## Milestone 11 corrective release — documentation matrix

| Field | Status |
|---|---|
| Date opened/completed | Completed 2026-07-30 |
| Source repository/SHA | `reblocke/conf_curve_likelihood` / `78d189ac03ec223a69778843497d27c70a8720c2` |
| Target repository/SHA | `reblocke/conf_curve_likelihood` / `427d425d16f847a9462ef0084d96841137995512` |
| Branch | `codex/mig-10-validation-matrix-docs` |
| Pull request | [#23](https://github.com/reblocke/conf_curve_likelihood/pull/23) |
| Tag/release | [v0.2.3 prerelease](https://github.com/reblocke/conf_curve_likelihood/releases/tag/v0.2.3) |
| Core version | Exact `wald-inference` v0.4.1 release |
| Validation status | Exact release independently reviewed; portfolio verdict remains owned by the catalog report |
| Intended behavior changes | Add required scientific-scope and validation records; no numerical or browser-contract change |
| Artifact/manifest hashes | Source archive `8a5a07687ba4b5cfa093266264a8911b2f56968b55e33ca0b772db07da4d82dd`; stage manifest `e16e0cbfe85a83bf1b347a3a606cc747136e6ef86288133bb2caa65f07a5d54f`; checksum file `d3844f4d39cfca845ec6452d2d7a6df640e40acaa49fbe8d2a5e8ea42f89f2b1` |

### Work recorded

- Add `docs/SCIENTIFIC_SCOPE.md` with the integrated question, conditioning distinction, formula
  authority, assumptions, limitations, and clinical-use boundary.
- Add `docs/VALIDATION.md` with frozen-baseline authority, exact tolerances, scientific ownership,
  browser/privacy/accessibility gates, commands, and evidence requirements.
- Reconcile this log and `METADATA_AUDIT.md` with the completed v0.2.1/v0.2.2 history.

### Validation evidence

- Main CI
  [run 30561596025](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30561596025)
  passed the locked test, B01-B08, Chromium, WebKit, staging, and clean-tree gates at
  `427d425d16f847a9462ef0084d96841137995512`.
- Pages
  [run 30561595983](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30561595983)
  deployed the same commit.
- Release
  [run 30562484672](https://github.com/reblocke/conf_curve_likelihood/actions/runs/30562484672)
  verified the annotated tag, reran all release gates, and published three checksum-verified
  assets. The live stage-manifest bytes equal the released manifest bytes.
- Independent post-tag review confirmed the v0.2.2-to-v0.2.3 diff changed documentation,
  version metadata, and policy assertions only; `core.py`, `design.py`, `models.py`,
  `web_contract.py`, defaults, payloads, and golden fixtures did not change.

### Unresolved decisions and remaining risks

- Version 0.2.4 reconciles these release facts and version surfaces only. It does not change
  scientific behavior, browser contracts, privacy, accessibility, or exports, and it makes no
  self-certifying claim about the portfolio verdict.

### Stable-Core publication correction — 2026-07-30

- The exact Core v0.4.1 release at
  `f4613177b6dc81d194aa70762152de2bfa86663b` is now a stable, non-draft GitHub release.
- Integrated releases remain experimental GitHub prereleases; stable Core status does not promote
  or clinically validate this application.
- Version 0.2.5 corrects this lifecycle wording and version-policy surfaces only. It does not alter
  formulas, golden responses, tolerances, Python/browser contracts, defaults, privacy,
  accessibility, UI behavior, or exports.
