# Contributing

## Ground rules

- Prefer **small, reviewable** pull requests.
- Keep the **computational core** pure; keep I/O in scripts/CLI layers.
- Update or add tests when behavior changes.
- If you make a design/assumption change, write it down in `docs/DECISIONS.md`.
- If you change dependencies, update `pyproject.toml` and `uv.lock` together.
- If you change the Python package consumed by the browser app, run the staging step before tests or review.
- For agent-assisted changes, check `AGENTS.md` and the matching `.agents/skills/` workflow before non-trivial edits.

## Definition of done

A PR is typically ready to merge when:

- `make fmt-check` is clean
- `make lint` is clean
- `make test` passes
- `make e2e` passes
- `make verify` passes for final integration checks
- staged web Python assets reflect `src/confcurve/`
- any behavior or architecture changes are documented in `docs/DECISIONS.md`

## Pull request checklist

- [ ] What is the user-facing or scientific goal of the change?
- [ ] What are the success criteria and how were they verified?
- [ ] Are new dependencies necessary? If yes, were they added via `uv add` and locked?
- [ ] Does the change keep paths relative (no hard-coded absolute paths)?
- [ ] Does the change avoid hidden state and non-determinism?
- [ ] If browser behavior changed, were Playwright checks or equivalent manual checks run?
