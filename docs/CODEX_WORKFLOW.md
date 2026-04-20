# Coding-agent workflow (Codex)

This repo is intended to be usable with a coding agent (Codex) without turning the codebase into an unreviewable blob.

## Default loop

1. **Frame**
   - restate the product and scientific goal
   - state assumptions and constraints
   - define acceptance tests

2. **Plan**
   - propose the smallest change set that satisfies the acceptance tests
   - identify touch points (files to change)

3. **Execute**
   - implement in small commits
   - keep side effects at the edges
   - update/add tests

4. **Evaluate**
   - run `make verify`
   - summarize what changed and why

## Repo-specific rules

- Read and follow `AGENTS.md`.
- Use focused workflows under `.agents/skills/` when the task matches a skill trigger.
- Record non-obvious choices in `docs/DECISIONS.md`.
- If `src/confcurve/` changes, run the staging step before browser verification.

## When you are stuck

- reduce scope
- write a failing test that captures the desired behavior
- add logging/diagnostics behind a flag
- document what you tried and why it failed
