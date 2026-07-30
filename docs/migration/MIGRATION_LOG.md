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

## Entry template

Copy this section for each later milestone:

```markdown
## Milestone NN — Title

| Field | Status |
|---|---|
| Date opened/completed | |
| Source repository/SHA | |
| Target repository/SHA | |
| Branch | |
| Pull request | |
| Tag/release | |
| Core version | |
| Validation status | |
| Intended behavior changes | |
| Artifact/manifest hashes | |

### Work recorded

- Pending.

### Validation evidence

- Command:
- Result:

### Unresolved decisions and remaining risks

- Pending.
```
