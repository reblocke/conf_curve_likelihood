# Scientific scope

## Integrated question

How do an observed estimate and reported two-sided 95% confidence interval look across
compatibility, normalized Wald relative-likelihood, and repeated-study design-calibration views
when those different questions must be compared deliberately in one workbench?

This is an educational and research-facing method tool for aggregate published estimates. It is
not a clinical calculator, diagnostic system, regulated device, or patient-specific
decision-support product.

## Two conditioning paradigms

The workbench intentionally contains two kinds of analysis that must not be conflated:

- **Observed-data reconstruction** evaluates candidate effect values against the estimate and
  standard error reconstructed from one reported confidence interval. Compatibility and
  normalized relative likelihood belong to this paradigm.
- **Design calibration** treats specified values as assumed true effects and evaluates the
  repeated-study behavior of a chosen Wald claim rule. Selected-claim probability, Type S, Type M,
  observed exaggeration, and inverse-precision targets belong to this paradigm.

The same numerical value can appear in both views, but its role differs. An observed-data
candidate is not an assumed truth, and a design-calibration probability is not a posterior
probability about the observed result.

## Inputs and working scales

The workbench accepts an effect measure, a reported two-sided 95% confidence interval, an optional
reported estimate, null and reference values, optional display bounds, and view/export controls.
Design views additionally require explicit choices about assumed true effects, selection rule,
alpha, claim direction or threshold when relevant, information multiplier, and optional precision
targets.

Additive effects use the identity working scale. Ratio effects use the natural logarithm and
therefore require strictly positive natural-scale values. On the working scale, the interval
midpoint determines the reconstructed estimate and its width determines the standard error using
the standard-normal 0.975 quantile.

Inputs should be aggregate published or synthetic method values. The application neither needs nor
is designed to receive identifiers or patient-level data.

## Outputs

Observed-data outputs include:

- the reconstructed estimate and standard error;
- a two-sided Wald compatibility curve;
- normalized Wald relative likelihood and log support;
- S-minus-2 and candidate support summaries;
- null and user-supplied reference summaries; and
- the retained closed-form 80% power benchmark, clearly labeled as a design aid rather than an
  exact critical-effect calculation.

Design outputs include:

- selected-claim probability under one of six explicit selection rules;
- Type S wrong-sign probability;
- Type M magnitude exaggeration on the working scale;
- observed exaggeration;
- information-scaled scenarios; and
- per-target inverse-precision results.

The browser also provides text and table alternatives plus CSV, dashboard PNG, manuscript PNG,
caption, and reviewer-text exports. Display bounds affect only the grid and presentation, not the
reconstructed summaries.

## Formula authority

All production statistical formulas are owned by the public root API or documented legacy adapter
of the exact released
[`wald-inference` 0.4.1](https://github.com/reblocke/wald-inference-core/releases/tag/v0.4.1)
artifact. The local `confcurve` package is a backward-compatible request/response adapter and
presentation layer; it does not fork the Core formulas.

Core owns:

- effect registration and identity/log transforms;
- confidence-interval midpoint and standard-error reconstruction;
- compatibility and normalized relative likelihood;
- support intervals and pairwise support ratios;
- legacy and exact detectability;
- selection rules and selected-claim probability;
- Type S, Type M, and observed exaggeration; and
- information scaling and precision solvers.

The integrated adapter preserves the pre-split `compute_curves()` contract, labels, ordering,
warnings, and undefined-value conventions. Browser-facing undefined quantities use JSON `null`;
nonfinite JSON values are rejected.

## Assumptions

- The reported limits represent a two-sided 95% interval.
- A one-parameter Wald approximation is reasonable on the registered working scale.
- Published rounding has not materially distorted midpoint or width reconstruction.
- A supplied estimate is compatible with the interval midpoint within the documented tolerance.
- Design results are conditional on the supplied true-effect scenario, fixed working-scale
  standard error or information multiplier, and the chosen claim rule.
- Reference thresholds are user-supplied scientific context; the app does not validate their
  clinical or policy meaning.

## Limitations and non-goals

- The workbench does not recover the exact fitted-model profile likelihood, raw study design,
  covariance structure, or variance estimator.
- Normalized relative likelihood is not posterior probability.
- Compatibility is not a probability that a candidate value is true.
- Type S and Type M are repeated-study operating characteristics, not probabilities that the
  observed estimate is wrong.
- The retained 80% benchmark is not the focused app's exact critical-effect solver and is not a
  meaningful-effect standard.
- An information multiplier is not automatically an exact sample-size multiplier without design
  assumptions.
- The app does not choose an MCID, assumed truth, selection rule, precision target, or direction of
  benefit.
- The workbench is feature-frozen except for Core upgrades, correctness, accessibility, security,
  browser compatibility, and contract-preserving maintenance. New focused capabilities belong in
  the focused repositories.
- It is not scientifically or clinically validated for treatment, diagnostic, regulatory,
  operational, or patient-specific decisions.

For a single question, use the
[focused Wald tools catalog](https://reblocke.github.io/wald-inference-tools/). The integrated
workbench remains available for intentional side-by-side comparison and backward compatibility.
