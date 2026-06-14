# Type S/M Design Calibration

## Purpose

The app has two separate interpretation layers:

1. The observed-evidence layer reconstructs the compatibility curve and normalized Wald relative likelihood from a reported estimate and 95% CI.
2. The design-calibration layer asks what repeated studies would look like if each candidate x-axis value were the true effect under a selected-claim rule and a chosen Wald standard error.

The same numeric x-axis can therefore have two readings in the figure. In observed panels, an x-value
is a candidate effect compared with the observed CI-derived reconstruction. In the design panels, that
same x-value is an assumed true effect used to compute repeated-study operating characteristics for
power, Type S, Type M, and observed exaggeration.

Type S and Type M complement the observed confidence and likelihood displays by showing how reliable selected claims would be under assumed true effects. They are not posterior probabilities that the observed estimate is wrong.

## Model

The design layer uses the same one-parameter normal/Wald model as the observed reconstruction:

```text
eta_true = candidate true effect on the working scale
eta_null = null value on the working scale
se       = design working-scale standard error
alpha    = selected-claim threshold
delta    = (eta_true - eta_null) / se
Z        = (future estimate - eta_null) / se ~ Normal(delta, 1)
```

The default design SE is the CI-implied working-scale SE. The optional information multiplier changes only the design SE:

```text
se_design = se_current / sqrt(information_multiplier)
```

This does not alter the observed confidence curve, p-value curve, relative-likelihood curve, CI reconstruction, or observed summaries.

## Selection Rules

The selected-claim rule defines which repeated-study results count as selected claims. The app supports:

- two-sided `p < alpha` against the null
- one-sided positive `p < alpha`
- one-sided negative `p < alpha`
- CI at selected alpha excludes the null in the selected claim direction
- estimate exceeds a claim threshold / MCID and two-sided `p < alpha`
- CI at selected alpha excludes a claim threshold / MCID

Threshold-conditioned rules require a threshold above the null for positive claims and below the null for negative claims. These thresholds are user-defined reference values; the app does not validate that they are clinically or scientifically justified.

The app distinguishes three user-facing inputs:

- reference thresholds/MCIDs are vertical markers and support-comparison rows for the observed evidence display
- claim thresholds/MCIDs define threshold-based selected-claim rules in design calibration
- assumed true-effect scenarios add design scenario rows and precision-target choices, but do not define selected-claim cutoffs

## Metrics

Selected-claim probability is the probability a future study would satisfy the selected-claim rule. For the default two-sided rule:

```text
c          = z_(1 - alpha / 2)
upper_tail = P(Z > c)  = sf(c - delta)
lower_tail = P(Z < -c) = cdf(-c - delta)
power      = upper_tail + lower_tail
```

For other rules, the same quantities are computed from exact normal tail intervals on the future Wald Z scale.

Type S is the conditional probability that a selected claim has the wrong sign relative to the assumed true-effect direction. Type M is the expected magnitude exaggeration among selected claims:

```text
TypeM = E(|Z| | selected) / |delta|
```

Observed exaggeration if true is a retrospective comparison, not Type M:

```text
observed_exaggeration = abs(eta_hat - eta_null) / abs(eta_true - eta_null)
```

The browser figure plots all four design metrics at once. Type M and observed exaggeration can grow
without bound near the null, so the plot omits ratio-curve values above `10x` to keep the visible
scale readable. This is display-only; scenario tables, CSV exports, and the JSON contract retain the
uncapped values.

## Precision Targets

Precision targets solve for the approximate Wald SE, 95% CI width, and information multiplier required to meet requested design criteria at a selected assumed true effect:

- target selected-claim probability, default `0.80` when a precision target effect is selected
- maximum Type S probability, optional
- maximum Type M exaggeration, optional and greater than `1`

The solver uses monotonic bisection over the design SE while recomputing the selected-claim rule. It returns a blank value and warning when no finite meaningful solution is bracketed, especially at or near the null or when a threshold rule cannot be satisfied by the chosen assumed true effect.

## Interpretation

Compatibility curves, confidence curves, p-value curves, and relative-likelihood curves condition on the observed data and evaluate candidate effect values.

Type S/M design calibration conditions on an assumed true effect and a selected-claim rule, then describes repeated-study behavior. The two layers can disagree without contradiction because they answer different questions.

Use wording such as:

```text
Using 1x the CI-implied Wald information and assuming a true effect of X, this design would have Y% selected-claim probability under RULE at alpha A. Conditional on a selected claim, the wrong-sign probability would be S% and the expected magnitude exaggeration would be Mx on the working scale. These are repeated-study operating characteristics under the assumed true effect, not posterior probabilities that the observed result is wrong.
```

## Ratio-Scale Handling

Additive effect measures use their natural working scale. Ratio measures use the log working scale:

- odds ratio
- risk ratio
- hazard ratio
- incidence rate ratio
- ratio of means

For ratio measures, Type M is an exaggeration ratio for the log-scale distance from the selected null ratio. It is not direct inflation of the natural-scale odds ratio, risk ratio, or hazard ratio.

## Undefined Values Near Null

Type S and Type M are blank at or very near the null. At the null, there is no true-effect direction for a wrong-sign claim, and the Type M denominator approaches zero.

The JSON contract returns `null` for undefined Type S, Type M, observed exaggeration, and unavailable precision-target values. Browser tables and CSV exports display blanks or "undefined" wording rather than `NaN` or `Infinity`.

## Limitations

- The design layer uses a one-parameter Wald approximation, not the original fitted model likelihood.
- Information multipliers are approximate one-parameter Wald precision scaling, not a replacement for a study-specific sample-size or power analysis.
- User thresholds and assumed true effects are reference values supplied by the user.
- The feature is educational/research interpretation software, not clinical decision support.

## Future Work

Future work may add URL/state persistence, more teaching examples, accessibility polish for advanced controls, and print-friendly design-calibration handouts. New selection workflows should continue to require numerical tests, UI wording, and decision records before exposure.
