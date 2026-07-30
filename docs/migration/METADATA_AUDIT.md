# Metadata Audit

## Scope and status

This inventory records repository metadata visible in the frozen source checkout at
`f77cd13f0286e933a66c0997af288a0dfa167bd5`. It deliberately preserves conflicts and
placeholders. It does not select an author, maintainer, or copyright holder for this
repository or any downstream repository.

## Inventory

| Surface | Recorded value | Status |
|---|---|---|
| GitHub repository | `reblocke/conf_curve_likelihood` | Confirmed by `origin` |
| Git remote | `https://github.com/reblocke/conf_curve_likelihood.git` | Confirmed locally |
| README title | `Wald Confidence Curve Explorer` | Consistent with `CITATION.cff` and HTML title |
| Package description | `Static GitHub Pages app and Python core for Wald confidence-curve reconstruction` | From `pyproject.toml`; live GitHub description not independently checked |
| Distribution name | `confcurve` | From `pyproject.toml` |
| Import package | `confcurve` | From `src/confcurve/` |
| Package version | `0.1.0` | From `pyproject.toml` |
| README maintainer | `Brian W. Locke` (`@reblocke`) | Conflicts with package/citation author |
| `pyproject.toml` author | `Reed Blocke` | Conflicts with README maintainer |
| `CITATION.cff` author | Given name `Reed`; family name `Blocke` | Conflicts with README maintainer |
| `CITATION.cff` title | `Wald Confidence Curve Explorer` | Consistent with README/HTML |
| `CITATION.cff` version | `0.1.0` | Consistent with package version |
| `CITATION.cff` release date | `2026-03-23` | Recorded; not changed by this audit |
| `CITATION.cff` repository | `https://github.com/reblocke/conf_curve_likelihood` | Consistent with `origin` |
| License identifier | MIT | Consistent across README, `CITATION.cff`, and `LICENSE` |
| License copyright line | `Copyright (c) 2026 Your Name` | Unresolved placeholder; do not infer a rights holder |
| Hosted app | `https://reblocke.github.io/conf_curve_likelihood/` | Documented in README; deployment not independently exercised by this audit |
| Release tags | None | Confirmed by local tag inventory on 2026-07-29 |

The audited Git commit records `Brian Locke` as its Git author/committer. Git commit identity
is provenance, not sufficient authority to replace the explicit package or citation
metadata.

## Approval boundaries

Two metadata questions require authoritative human resolution before a stable
`wald-inference-core` release and before identity is propagated across the portfolio:

1. Should the canonical public author/maintainer identity be **Reed Blocke**, **Brian W.
   Locke**, or another exact form?
2. What exact copyright-holder text, if any, should replace `Your Name` in the existing MIT
   license and in new repositories?

Until answered:

- do not harmonize names by majority, Git history, the GitHub handle, or inference;
- do not replace the license placeholder;
- do not publish a new stable package/release under an assumed identity; and
- carry the conflict explicitly in migration handoffs.

The MIT license choice itself is not in conflict. The unresolved issue is attribution and
the copyright-holder line, not the operative license text.

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

## Required follow-up

After the human metadata decision:

1. record the authoritative instruction and date in the relevant decision log;
2. update package, citation, README, and license metadata deliberately and consistently;
3. propagate the approved form to new repositories rather than copying the present conflict;
4. verify hosted/repository descriptions through the GitHub interface; and
5. record release tags and release URLs as they are created.
