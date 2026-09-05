# Coding-agent workflow (Codex)

Use `AGENTS.md` for repository boundaries and select a focused workflow under `.agents/skills/` when it helps the current task. A skill trigger is not a requirement to perform an unrelated planning or audit workflow.

- Read the documentation and entry points governing the affected behavior. Resolve consequential scientific or interface choices before dependent edits.
- Complete authorized local implementation, applicable verification, and regression fixes. Commit only when the user requests it.
- Documentation-only changes need affected-reference checks and `git diff --check`.
- Code changes need affected tests; use `make verify` when impact spans the repository. Preserve the complete Core upgrade and release gates in `docs/CORE_UPGRADE_CHECKLIST.md` and `docs/VALIDATION.md`.
- If `src/confcurve/` changes, run `make stage-web` before browser verification; never hand-edit generated browser Python.
- Record non-obvious behavior or architecture choices in `docs/DECISIONS.md` and update affected public documentation.
- Report verification evidence and any unresolved gates without claiming scientific or clinical validation beyond that evidence.
