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
| Date opened | 2026-07-29 |
| Source repository | `reblocke/conf_curve_likelihood` |
| Target repository | `reblocke/conf_curve_likelihood` |
| Source branch/SHA | `main` at `f77cd13f0286e933a66c0997af288a0dfa167bd5` |
| Working branch | `codex/mig-00-freeze-baseline` |
| Audited-versus-actual comparison | Identical; no commits after the audited SHA at inspection |
| Pull request | [#11](https://github.com/reblocke/conf_curve_likelihood/pull/11) (draft) |
| Baseline tag | Pending; intended `pre-split-baseline-2026-07-29` after verification and merge |
| Core version | Not applicable; numerical code is still integrated in `confcurve` |
| Validation status | Draft harness verified; release blocked by the known strict-JSON extreme-design defect |
| Intended production behavior changes | None |
| Fixture manifest/hash | Draft manifest `116dcdea29a592b60a26e478a5a0f40e2ad1e88e71b99a8a5c0beb6f2ed466df`; fixture set `4ecf8afa100941cf76be847703429409c4b739d9a6012a5e4757328a012bb943` |
| Release notes/release URL | Pending |

### Work recorded

- Selected the exact audited source commit as the behavior-freeze source.
- Added repository-local migration documentation and metadata inventory.
- Recorded the target architecture without moving formulas or changing production behavior.
- Generated 21 B01–B08 cases, machine-readable contract/export schemas, an exact effect
  registry snapshot, and deterministic comparison tooling.
- Added exact downloaded CSV-header and PNG-dimension browser gates.

### Draft validation evidence

- `make verify` passed after the initial hardened corpus and browser export checks.
- The current post-review corpus passed its 22-test focused integration suite, generator
  check, comparator, Ruff format/lint checks, and `git diff --check`.
- A final full run remains required after the approved behavior source is known.

### Unresolved decisions

- Canonical public identity: package/citation metadata say `Reed Blocke`; README says
  `Brian W. Locke`; the audited Git commit says `Brian Locke`.
- The MIT license contains the unresolved copyright placeholder `Your Name`.
- [Issue #12](https://github.com/reblocke/conf_curve_likelihood/issues/12) records an
  accepted extreme design request that emits nonfinite standardized distances. The
  proposed isolated fix is to reject an unrepresentable distance with `ValidationError`;
  it requires explicit approval before production code changes.
- Final tag target, post-fix fixture hashes, final full verification, PR, and release remain
  pending.

### Completion evidence to append

When completed, record:

1. merged commit and expected-head confirmation;
2. fixture case inventory and manifest SHA-256;
3. exact comparator tolerances;
4. commands run and their results;
5. confirmation that production files and behavior did not intentionally change;
6. CI results, tag target, tag URL, and release URL; and
7. remaining risks or approved deviations.

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
