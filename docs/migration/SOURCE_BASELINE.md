# Integrated Source Baseline

## Status

This document records the approved source selected for the pre-split behavior freeze and
the released golden corpus. The strict-JSON release gate, canonical metadata decision,
expected-head merge, annotated tag, and GitHub release are complete.

| Item | Recorded value |
|---|---|
| Repository | `reblocke/conf_curve_likelihood` |
| Remote | `https://github.com/reblocke/conf_curve_likelihood.git` |
| Source branch | `main` |
| Audited SHA | `f77cd13f0286e933a66c0997af288a0dfa167bd5` |
| Actual behavior-freeze source SHA | `830756ecb11b4e8161f8dfe1fc75afc346ef4467` |
| Migration working branch | `codex/mig-00-freeze-baseline` |
| Inspection date | 2026-07-29 |
| Pull request | [#11](https://github.com/reblocke/conf_curve_likelihood/pull/11) |
| Baseline merge SHA | `5fd501dd947d9b951d736014cfc2b310efa5e7b0` |
| Tag | [`pre-split-baseline-2026-07-29`](https://github.com/reblocke/conf_curve_likelihood/releases/tag/pre-split-baseline-2026-07-29) |
| Tag status | Annotated tag verified to resolve to the baseline merge SHA |
| Release | [Pre-split integrated baseline (2026-07-29)](https://github.com/reblocke/conf_curve_likelihood/releases/tag/pre-split-baseline-2026-07-29) |
| Golden generation status | Final corpus generated: 22 cases and 50 deterministic JSON artifacts |
| Successful generation date | 2026-07-29 |
| Manifest SHA-256 | `f54bb2d8311788c07adcf23fc9f038e35702449e4a77a474abea9411246cabcc` |
| Fixture-set SHA-256 | `81c341b39e711caffc85a444f0c1e4bc1e2d00633474c82e720afeb60def3c4d` |

At initial inspection, local `main`, `origin/main`, and `origin/HEAD` all resolved to the
audited SHA, the working tree was clean, and `git log
f77cd13f0286e933a66c0997af288a0dfa167bd5..HEAD` was empty. The migration branch was
created from that SHA.

Two explicitly authorized changes were then merged before final fixture generation:

- `9d59fd9e17900ef177e695ba3a34ccc0a08e374b` (PR #13) canonicalized public metadata as
  `Brian Locke` and retained the MIT License.
- `830756ecb11b4e8161f8dfe1fc75afc346ef4467` (PR #14) fixed the strict-JSON
  floating-point boundary defect recorded in issue #12.

The second commit is the final behavior source. Its only intentional production difference
from the audited SHA is the approved finite-range safety behavior: representable
opposite-sign standardized distances are recovered, unrepresentable derived values raise
`ValidationError`, and every successful response contains only finite JSON numbers.
Ordinary representable arithmetic and all protected formulas remain unchanged.

The behavior source SHA and eventual tag target serve different purposes:

- The behavior source SHA identifies the production implementation from which fixtures are
  generated.
- The eventual tag may identify a later merged milestone-00 commit containing the fixtures,
  tests, and migration documentation, provided production behavior remains unchanged and
  all gates pass.

The final fixture manifest stamps the behavior source SHA above. Fixtures are generated
outputs from that recorded source, not independently authored expected values.

## Recorded environment

The local interpreter and locked or browser-pinned versions observed on 2026-07-29 were:

| Component | Version | Authority |
|---|---:|---|
| Python | 3.11.10 | Existing `.venv`; `.python-version` selects Python 3.11 |
| NumPy | 2.2.6 | `uv.lock` |
| SciPy | 1.14.1 | `uv.lock` |
| pytest | 9.0.2 | `uv.lock` |
| Hypothesis | 6.151.9 | `uv.lock` |
| Playwright | 1.58.0 | `uv.lock` |
| pytest-playwright | 0.7.2 | `uv.lock` |
| Ruff | 0.15.1 | `uv.lock` |
| Pyodide | 0.29.3 | `web/assets/config.js` and `web/index.html` |
| Plotly.js | 3.1.0 | `web/index.html` |

Pyodide and Plotly are browser bundle pins; they are not Python packages resolved by
`uv.lock`. Browser and local numerical results must therefore use the comparison tolerance
appropriate to their execution environments rather than assuming identical dependency
stacks.

## Existing automation

The repository has two GitHub Actions workflows:

- `CI` in `.github/workflows/ci.yml`, with Python checks, a full Chromium E2E job, and a
  WebKit initial-load smoke job.
- `Deploy Pages` in `.github/workflows/pages.yml`, which stages the Python package and
  deploys `web/` from `main`.

The existing Make targets are:

```text
make stage-web
make fmt-check
make lint
make golden-check
make test
make e2e
make verify
make serve
```

`make verify` currently exercises the Chromium E2E suite; the WebKit smoke path is a
separate CI job.

## Milestone-00 verification contract

The following commands are the required completion sequence once the golden scripts and
fixtures exist:

```bash
uv sync --locked
uv run playwright install chromium webkit
make verify
uv run python scripts/generate_golden_baseline.py --check
uv run python scripts/compare_golden_baseline.py
git diff --check
git status --short
```

No command above is recorded as passing merely by appearing here. The migration log must be
updated with commands, results, fixture manifest hash, verified commit, and tag only after
they are actually observed.

## Verification evidence

On 2026-07-29, the draft harness passed `make verify`, the focused golden integration suite
(22 tests), generator check, comparator, Ruff checks, and `git diff --check`. PR #14 then
passed its complete local `make verify`, focused Chromium and WebKit boundary regressions,
100,000 ordinary bit-for-bit arithmetic comparisons, a 972-payload boundary sweep, and all
GitHub CI jobs.

The final 22-case corpus was regenerated from the approved source SHA. The completion
sequence then passed:

- `uv sync --locked`;
- `uv run playwright install chromium webkit`;
- `make verify`, including 157 non-E2E tests and 43 Chromium E2E tests;
- the 22-case generator check and recursive comparator at `rtol=1e-12`, `atol=1e-14`;
- Ruff format and lint checks; and
- `git diff --check`.

PR #11's exact reviewed head
`d6c709d9f7bcf09a156295e09025c8f8bfd3d923` passed both GitHub unit jobs, both full
Chromium jobs, and both WebKit smoke jobs. It was then squash-merged with expected-head
protection as `5fd501dd947d9b951d736014cfc2b310efa5e7b0`. The annotated tag and public
release were verified to resolve to that merge commit.

## Tagging rule

The tag is `pre-split-baseline-2026-07-29`; no existing tags were present at inspection.
It was created only after:

1. the fixture corpus and comparator are committed;
2. the full local and CI gates pass;
3. the milestone branch is merged at the expected reviewed head; and
4. the exact tag target and fixture manifest hash are recorded.

The final annotated tag object is `58855d85227864efb30b7e66a79c28cb13103608`; its
peeled commit is `5fd501dd947d9b951d736014cfc2b310efa5e7b0`.
