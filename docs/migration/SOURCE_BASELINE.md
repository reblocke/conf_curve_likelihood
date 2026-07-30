# Integrated Source Baseline

## Status

This document records the source selected for the pre-split behavior freeze and the current
draft golden corpus. It does not claim that the strict-JSON release gate, merge, tagging, or
release have completed.

| Item | Recorded value |
|---|---|
| Repository | `reblocke/conf_curve_likelihood` |
| Remote | `https://github.com/reblocke/conf_curve_likelihood.git` |
| Source branch | `main` |
| Audited SHA | `f77cd13f0286e933a66c0997af288a0dfa167bd5` |
| Actual behavior-freeze source SHA | `f77cd13f0286e933a66c0997af288a0dfa167bd5` |
| Migration working branch | `codex/mig-00-freeze-baseline` |
| Inspection date | 2026-07-29 |
| Intended tag | `pre-split-baseline-2026-07-29` |
| Tag status | Pending full verification, merge, and confirmation of the tagged commit |
| Golden generation status | Draft generated: 21 cases and 48 deterministic JSON artifacts |
| Successful generation date | 2026-07-29 (draft; the global strict-JSON gate remains blocked) |
| Draft manifest SHA-256 | `116dcdea29a592b60a26e478a5a0f40e2ad1e88e71b99a8a5c0beb6f2ed466df` |
| Draft fixture-set SHA-256 | `4ecf8afa100941cf76be847703429409c4b739d9a6012a5e4757328a012bb943` |

At inspection, local `main`, `origin/main`, and `origin/HEAD` all resolved to the audited
SHA, the working tree was clean, and `git log
f77cd13f0286e933a66c0997af288a0dfa167bd5..HEAD` was empty. There are therefore no
post-audit commits to reconcile for the behavior freeze. The migration branch was created
from that same SHA.

The behavior source SHA and eventual tag target serve different purposes:

- The behavior source SHA identifies the production implementation from which fixtures are
  generated.
- The eventual tag may identify a later merged milestone-00 commit containing the fixtures,
  tests, and migration documentation, provided production behavior remains unchanged and
  all gates pass.

The draft fixture manifest stamps the behavior source SHA above. Fixtures are generated
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

## Draft verification evidence and open gate

On 2026-07-29, `make verify` passed after the golden harness and exact browser-export
assertions were added. After the final manifest portability and effect-registry hardening,
the focused golden integration suite (22 tests), generator check, comparator, Ruff checks,
and `git diff --check` passed. The full suite will be rerun after the pending strict-JSON
safety decision because that approved fix, if accepted, changes the behavior source SHA and
requires fixture regeneration.

The exact accepted request and failure mode are documented in `CURRENT_BEHAVIOR.md`.
Milestone 00 cannot be tagged while that request can emit nonfinite browser payload values.

## Tagging rule

The intended tag is `pre-split-baseline-2026-07-29`; no existing tags were present at
inspection. Do not create or report that tag until:

1. the fixture corpus and comparator are committed;
2. the full local and CI gates pass;
3. the milestone branch is merged at the expected reviewed head; and
4. the exact tag target and fixture manifest hash are recorded.

If the preferred tag appears before completion, use a clearly versioned variant and record
the reason in `MIGRATION_LOG.md`.
