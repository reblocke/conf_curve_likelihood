# Metadata Audit

## Scope and status

This inventory records both the conflicting metadata visible at audited commit
`f77cd13f0286e933a66c0997af288a0dfa167bd5` and its authoritative resolution. On
2026-07-29, the repository owner explicitly selected `Brian Locke` as the canonical public
name and approved retaining the MIT License. PR #13 applied that decision at
`9d59fd9e17900ef177e695ba3a34ccc0a08e374b`.

Ticket 10 and its Milestone 11 corrective releases refreshed the product/version surfaces on
2026-07-30 while preserving that identity decision. The table below reports the reconciled
post-v0.2.3 release state carried by the documentation-only v0.2.4 patch; the original conflicts
remain described as provenance.

The historical conflict remains recorded here as provenance: the README used `Brian W.
Locke`, package and citation metadata used `Reed Blocke`, and the license used the
placeholder `Your Name`.

## Inventory

| Surface | Recorded value | Status |
|---|---|---|
| GitHub repository | `reblocke/conf_curve_likelihood` | Confirmed by `origin` |
| Git remote | `https://github.com/reblocke/conf_curve_likelihood.git` | Confirmed locally |
| GitHub visibility/license | Public; MIT detected | Verified through GitHub on 2026-07-29 |
| GitHub description | `Integrated Wald inference workbench for compatibility, normalized relative likelihood, and design calibration` | Verified through GitHub on 2026-07-30 |
| GitHub homepage field | `https://reblocke.github.io/conf_curve_likelihood/` | Verified through GitHub on 2026-07-30 |
| README title | `Integrated Wald Inference Workbench` | Consistent with `CITATION.cff` and HTML title |
| Package description | `Static GitHub Pages app and compatibility adapter for Wald inference` | From `pyproject.toml`; distinct from the verified live GitHub description above |
| Distribution name | `confcurve` | From `pyproject.toml` |
| Import package | `confcurve` | From `src/confcurve/` |
| Package version | `0.2.4` | From `pyproject.toml` |
| README maintainer | `Brian Locke` (`@reblocke`) | Canonical form applied by PR #13 |
| `pyproject.toml` author | `Brian Locke` | Canonical form applied by PR #13 |
| `CITATION.cff` author | Given name `Brian`; family name `Locke` | Canonical form applied by PR #13 |
| `CITATION.cff` title | `Integrated Wald Inference Workbench` | Consistent with README/HTML |
| `CITATION.cff` version | `0.2.4` | Consistent with package version |
| `CITATION.cff` release date | `2026-07-30` | Consistent with changelog release heading |
| `CITATION.cff` repository | `https://github.com/reblocke/conf_curve_likelihood` | Consistent with `origin` |
| License identifier | MIT | Consistent across README, `CITATION.cff`, and `LICENSE` |
| License copyright line | `Copyright (c) 2026 Brian Locke` | Approved MIT attribution applied by PR #13 |
| Hosted app | `https://reblocke.github.io/conf_curve_likelihood/` | Consistent across README, GitHub homepage, and deployment policy |
| Verified release tags through the evidence reconciliation | `pre-split-baseline-2026-07-29`, `v0.1.1`, `v0.2.0`, `v0.2.1`, `v0.2.2`, `v0.2.3` | v0.2.3 annotated tag, release assets, Pages commit, and workflows verified on 2026-07-30 |

The audited Git commit also records `Brian Locke` as its Git author/committer, but that
provenance was not treated as authority; the explicit owner instruction is the controlling
decision.

## Resolved propagation rule

- Use exact public name `Brian Locke` in package, citation, README, and maintainer metadata.
- Retain the MIT License and use `Copyright (c) 2026 Brian Locke`.
- Preserve `@reblocke` and existing repository URLs where applicable.
- Propagate these values to new portfolio repositories unless a later explicit decision
  supersedes them.
- Do not infer middle initials, pseudonyms, or alternative copyright text.

## Source references presently documented

The README and `docs/DECISIONS.md` identify these terminology or methodology sources:

- Zampieri et al., *American Journal of Respiratory and Critical Care Medicine* (2025), for
  evidential likelihood, likelihood ratios, support, and S−2 intervals; repository
  retrieval date 2026-04-23:
  `https://academic.oup.com/ajrccm/article/211/9/1610/8300617`
- Perugini et al., *Advances in Methods and Practices in Psychological Science* (2025), for
  critical-effect-size values and design-interpretation rationale; repository retrieval
  date 2026-04-23:
  `https://journals.sagepub.com/doi/10.1177/25152459251335298`
- Gelman and Carlin (2014), for Type S error, Type M exaggeration, and design calculations;
  repository retrieval date 2026-06-14:
  `https://journals.sagepub.com/doi/abs/10.1177/1745691614551642`

This audit does not re-evaluate those papers, their licenses, or the scientific claims they
support. No external figure, table, or substantial copied text is introduced by these
migration documents.

## Portfolio-verdict boundary

The independent report in `reblocke/wald-inference-tools` is authoritative for the portfolio
verdict. This repository records its release facts but does not self-certify portfolio validation.
No unresolved authorship or license decision remains.
