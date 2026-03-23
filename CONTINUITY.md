# Continuity ledger

Use this file to maintain continuity across coding sessions (human or agent).

## Current status

- Goal: Build the Wald Confidence Curve Explorer as a static GitHub Pages app with a Python numerical core staged into Pyodide.
- Last known good commit: UNCONFIRMED
- Next step: Finish the numerical package, stage it into `web/assets/py/confcurve/`, and wire the browser shell to it.

## Session log

### 2026-03-23

**Objective:**

Realign the starter repository into the confidence-curve app repository and implement the first end-to-end version.

**Plan:**

- replace starter-specific docs, package structure, and CI assumptions
- implement the validated numerical core with `numpy` and `scipy`
- wire the static web UI to Pyodide and Plotly
- add unit, property, integration, and browser tests

**Work completed:**

- created the `codex/wald-confcurve-applet` branch
- removed the conflicting starter pipeline and Stata codepaths
- added the static `web/` shell with pinned Plotly and Pyodide assets
- rewrote the top-level project framing and decision log for the app

**Verification:**

- pending for the foundation checkpoint

**Open questions / risks:**

- browser runtime performance depends on Pyodide + SciPy startup cost
- GitHub Pages is not configured yet and will be added later in the implementation
