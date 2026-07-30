# Current Behavior Inventory

This document freezes the integrated application's behavior at final behavior source commit
`830756ecb11b4e8161f8dfe1fc75afc346ef4467`. It is an inventory of the live Python and
browser contracts, not a proposal to change them. `src/confcurve/` remains the numerical
source of truth.

## Product boundary

The application combines two interpretation layers in one static browser interface:

1. **Observed evidence.** Candidate effect values are evaluated against a one-parameter Wald
   reconstruction derived from a reported 95% confidence interval.
2. **Design calibration, when enabled.** The same displayed x-values are treated as assumed true
   effects that generate repeated studies under a selected-claim rule and hypothetical Wald
   standard error.

The shared numeric axis does not make these conditioning statements interchangeable. Reference
thresholds on the observed display, claim thresholds used by a design selection rule, and assumed
true-effect scenarios are separate inputs.

## Effect registry and working scales

| Effect key | Display label | Family | Working scale | Default null |
|---|---|---|---|---:|
| `odds_ratio` | Odds ratio | ratio | log | 1 |
| `risk_ratio` | Risk ratio | ratio | log | 1 |
| `hazard_ratio` | Hazard ratio | ratio | log | 1 |
| `incidence_rate_ratio` | Incidence rate ratio | ratio | log | 1 |
| `ratio_of_means` | Ratio of means | ratio | log | 1 |
| `mean_difference` | Mean difference | additive | identity | 0 |
| `risk_difference` | Risk difference | additive | identity | 0 |
| `rate_difference` | Rate difference | additive | identity | 0 |
| `regression_coefficient` | Regression coefficient | additive | identity | 0 |

All natural-scale inputs for ratio measures must be strictly positive. Ratio calculations use log
values but the browser displays natural ratio values. Additive calculations and displays use the
identity scale.

## Observed-evidence reconstruction

The reported interval is always interpreted as a 95% interval.

- The working-scale estimate is the midpoint of the two CI limits. This is the arithmetic midpoint
  for additive measures and the log midpoint, displayed as the geometric mean, for ratio measures.
- An optional point estimate is validation input. It must agree with the CI midpoint within the
  larger of `1e-12` and 2% of the working-scale CI half-width. It does not replace the midpoint used
  for the curves or summaries.
- The working-scale standard error is the CI half-width divided by `z_(0.975)`.
- A supplied estimate can generate a warning when the two CI sides differ by more than the 2%
  asymmetry tolerance. The production browser reconstruction remains anchored to the CI midpoint
  and width.
- The null defaults to the effect registry value when absent. Reference thresholds are optional,
  finite candidate values and do not change the reconstruction.

For a candidate working-scale value `theta`:

```text
z(theta)                    = (theta - theta_hat) / SE
compatibility(theta)        = 2 * Normal.sf(abs(z(theta)))
relative_likelihood(theta)  = exp(-0.5 * z(theta)^2)
log_relative_likelihood     = -0.5 * z(theta)^2
```

Relative likelihood is normalized to 1 at the CI-implied estimate. It is a reconstructed normalized
Wald relative likelihood, not the exact fitted-model profile likelihood.

### Observed grid

Without a user display range, the working-scale grid:

- is symmetric around the CI-implied estimate;
- defaults to 801 odd-numbered points and a span of 4.5 standard errors;
- expands, with 0.25 SE padding, to include the null, reference thresholds, and paired 80% power
  benchmark markers; and
- can be truncated to protect finite floating-point values.

With a plausible display range, the grid uses the exact requested endpoints. The range changes only
the plotted and exported grid. It does not change the estimate, SE, CI/null/threshold summaries,
S−2 interval, 80% benchmark calculations, or design inputs. The application warns when important
markers fall outside that window.

### Observed summaries

The response payload contains:

- display- and working-scale estimate, CI, and null;
- estimate source and SE reconstruction method;
- working-scale SE and null standardized distance;
- null compatibility/two-sided Wald p-value;
- null relative and log relative likelihood;
- MLE-to-null likelihood ratio and log ratio, with overflow represented explicitly;
- paired 80% power benchmark markers around the null;
- display-range state; and
- threshold-support summaries.

Each threshold-support summary contains the display and working values, relative and log relative
likelihood versus the estimate, MLE-to-threshold support ratio and log ratio, threshold-to-null
support ratio and log ratio when finite, and direction relative to the estimate and null.

The visible summary presents a subset: display estimate and CI, null relative likelihood,
MLE-to-null ratio, two-sided p-value, one relative-support row per threshold, estimate source,
working-scale SE, computation scale, benchmark range, and active display range. Working-scale
estimate/CI/null values, null Z, log likelihood fields, and the remaining threshold fields are
response-only. The main takeaway uses the first threshold; the visible summary lists every
threshold.

The qualitative null-support wording is:

- relative likelihood at least 0.5: “substantial support”;
- at least 0.1: “moderate support”;
- at least 0.01: “limited support”; and
- below 0.01: “very weak support.”

### S−2 support interval and 80% benchmarks

The S−2 interval is present in every response and is shown when the likelihood panel is visible:

```text
support cutoff             = -2
relative-likelihood cutoff = exp(-2)
working-scale endpoints    = theta_hat +/- 2 * SE
MLE:boundary ratio         = exp(2), approximately 7.4
```

The paired 80% power benchmark markers are:

```text
null_working +/- (z_(0.975) + z_(0.80)) * SE
```

They are fixed `alpha = 0.05`, `power = 0.80` design-interpretation markers. They are not a
generalized exact critical-effect calculation or a study-specific power analysis.

## Optional design-calibration behavior

Design calibration is disabled by default. When enabled:

```text
SE_design = SE_current / sqrt(information_multiplier)
delta     = (true_effect_working - null_working) / SE_design
```

The information multiplier changes only forward design calculations. Observed reconstruction is
unchanged. The inverse precision table compares required precision with the current CI-implied SE,
not with an already multiplied design SE.

The six supported selected-claim rules are:

1. two-sided `p < alpha` against the null;
2. one-sided positive `p < alpha`;
3. one-sided negative `p < alpha`;
4. CI at selected alpha excludes the null in the selected direction;
5. estimate crosses a claim threshold in the selected direction and two-sided `p < alpha`; and
6. CI at selected alpha excludes a directional claim threshold.

Threshold-conditioned positive claims require a claim threshold above the null; negative claims
require one below the null. One-sided positive and negative rules force their corresponding
direction.

For every grid value treated as the true effect, the design block reports:

- selected-claim probability, labeled `power` in the current contract;
- Type S wrong-sign probability conditional on selection;
- Type M expected magnitude exaggeration conditional on selection;
- expected selected absolute Wald Z; and
- observed exaggeration, using the CI-implied estimate as the retrospective observed value.

Type M is a ratio of working-scale distances from the null. For ratio measures it is therefore
defined on the log scale, not as direct inflation of a natural odds, risk, hazard, incidence-rate,
or means ratio.

### Scenario rows

Scenario rows are assembled in this stable priority order:

1. null;
2. CI-implied estimate as an explicitly optimistic/circular assumed truth;
3. observed reference thresholds; and
4. custom assumed true effects.

Duplicate working-scale values are removed with a relative tolerance of approximately `1e-10`.
Rows report assumed true effect, source/note, standardized delta, selected-claim probability, Type S,
Type M, and observed exaggeration.

### Inverse precision targets

The precision-target chooser is populated only from observed reference thresholds and custom assumed
true effects. Selecting a target creates a power target of 0.80 by default; maximum Type S and Type M
constraints are optional.

For each requested target, the response reports the required Wald SE, required information
multiplier, approximate 95% working-scale CI width, achieved metrics, and a status note. The solver
uses monotonic bisection, caps the supported information multiplier at `1e12`, reports multiplier 1
when current precision already suffices, and returns no finite solution rather than inventing one.

## Response and undefined-value conventions

The top-level browser response has stable ordered blocks:

```text
meta
summary
warnings
grid
design
```

`design` is `null` when calibration is disabled. Nonfinite inferential quantities are represented
with `null`, zero where zero is the actual limiting value, or a finite clipped display value
accompanied by a warning. Every successful browser response excludes `NaN`, `Infinity`, and
`-Infinity`.

For finite inputs whose required standardized design distance is not representable in binary64,
`compute_curves()` raises `ValidationError` before operating characteristics or browser JSON are
returned. The approved boundary fix in PR #14 recovers representable opposite-sign subtraction
overflow with power-of-two scaling while preserving the original direct arithmetic path for
ordinary representable inputs.

`null` is used for:

- Type S, Type M, and observed exaggeration at or within `1e-12` standardized units of the null;
- Type S when selected-claim probability is zero;
- expected selected absolute Z and Type M when no selected result has positive probability;
- unavailable or infeasible precision-target values;
- exponentiated likelihood ratios that exceed finite floating-point range; and
- null Z/log summaries when the null is too distant to compute a finite standardized value.

The UI renders these values as “undefined,” “not available,” an overflow explanation, an em dash, or
a blank CSV cell, depending on context. It does not silently convert undefined values to zero.

## Warnings and blocking validation

The “Technical reconstruction notes” list combines fixed explanatory notes with response warnings.
Warnings can report:

- identity versus log working scale and natural-axis spacing;
- SE method and asymmetric/non-Wald-looking intervals;
- active display ranges and excluded estimate, CI, null, threshold, or benchmark markers;
- finite-range grid truncation or collapse;
- natural-axis and S−2 endpoint clipping;
- null likelihood-summary overflow;
- reference-threshold, compatibility-guide, and S−2 overlay interpretation;
- assumed-true-effect conditioning and the selected-claim rule;
- Type S/M undefined behavior near the null;
- ratio-scale Type M semantics;
- display-only design plausible ranges;
- design-only information scaling;
- values above 10x omitted from ratio-valued design plots while retained in data; and
- precision targets without a finite solution.

Invalid inputs are errors, not warnings. They clear the rendered plot and summaries and disable
exports. Blocking cases include missing or unordered CI limits, nonfinite values, nonpositive ratio
inputs, a mismatched point estimate, incomplete or unordered ranges, fewer than 101 grid points,
invalid alpha/target values, nonpositive information, unsupported rules or directions, and missing
or misdirected claim thresholds. Many observed-curve and display ranges that are too extreme for
safe finite evaluation are also blocked. This includes unrepresentable finite standardized design
distances, which raise `ValidationError` before a browser response is serialized.

## Privacy and data path

- The deployed product is a static GitHub Pages application with no backend or database.
- Inputs are aggregate numerical estimates and settings held in the page DOM and in-memory Pyodide
  runtime. The JavaScript-to-Python JSON call occurs within the browser.
- The page makes static network requests for pinned Pyodide and Plotly assets, Pyodide's NumPy/SciPy
  packages, and same-origin staged `confcurve` source files. User-entered values are not appended to
  those requests.
- The application contains no analytics, telemetry, user accounts, cookies, URL/query/hash state,
  local storage, session storage, IndexedDB, or automatic upload.
- CSV/PNG downloads and caption/reviewer clipboard copies are explicit local user actions.
- No study dataset or patient-level record is expected or committed. The app should not be used to
  enter or store protected health information.

Third-party CDNs necessarily receive ordinary static-asset request metadata such as IP address and
browser headers. The current privacy claim is therefore “no transmission of entered numerical
values,” not “no network requests.”

## Non-goals

The current application does not:

- recover an exact fitted-model profile likelihood;
- infer the original model, design, variance estimator, sample-size formula, or effective sample
  size;
- verify that a reported interval is truly Wald-based beyond consistency/asymmetry checks;
- support arbitrary reported CI levels;
- provide Bayesian posterior probabilities or Bayes factors;
- interpret Type S/M as posterior probabilities about the observed result;
- validate a user-entered MCID or other threshold;
- provide clinical decision support, treatment recommendations, medical-device functionality, or
  clinical validation;
- turn an information multiplier into an exact sample-size multiplier;
- replace a study-specific power or sample-size analysis;
- save, share, synchronize, or transmit projects; or
- provide accounts, a backend, telemetry, or persistent browser state.

## Implementation authority

This inventory was traced to:

- `src/confcurve/models.py`
- `src/confcurve/core.py`
- `src/confcurve/design.py`
- `src/confcurve/web_contract.py`
- `web/index.html`
- `web/assets/config.js`
- `web/assets/app.js`
- `web/assets/renderers.js`
- `web/assets/plot.js`
- `web/assets/plot-helpers.js`
- `web/assets/runtime.js`
- `tests/`
