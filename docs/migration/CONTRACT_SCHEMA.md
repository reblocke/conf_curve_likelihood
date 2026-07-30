# Frozen Browser Contract Schema

## Status and authority

This document records the `compute_curves()` request and response contract at behavior
source commit `f77cd13f0286e933a66c0997af288a0dfa167bd5`. The static type authority is
`src/confcurve/models.py`; runtime defaults, conversion, construction, and insertion order
come from `src/confcurve/web_contract.py`.

The response must serialize with:

```python
json.dumps(response, allow_nan=False)
```

Undefined or unavailable inferential quantities use `None`/JSON `null`, never NaN or
Infinity. An empty list means an applicable collection has no rows; `null` means an
optional block or value is unavailable or disabled.

This is the intended contract. The frozen source has one accepted extreme-design request
that instead emits nonfinite standardized distances, as reproduced in
`CURRENT_BEHAVIOR.md`. That contradiction is an explicit release blocker pending an
approved production safety fix; it is not a supported exception to the schema.

## Scale and ownership vocabulary

| Term | Contract |
|---|---|
| Display scale | Natural scale for a ratio effect only when `display_natural_axis` is active; otherwise the working scale. Additive display and working values are numerically identical. |
| Working scale | Identity for additive effects; natural log for ratio effects. Ratio natural-scale inputs must be positive. |
| Standardized scale | Dimensionless Z or delta: a working-scale distance divided by a working-scale SE. |
| Observed evidence | Candidate values evaluated against the estimate and SE reconstructed from the reported 95% CI. |
| Repeated-study design | Candidate x-values treated as assumed true effects generating future Wald estimates under a selected-claim rule. |
| Probability | Dimensionless value in `[0, 1]`. |
| Fold ratio | Dimensionless likelihood, information, Type M, or exaggeration ratio. |

Reference thresholds belong to the observed comparison unless separately reused as
assumed-truth scenarios. A design claim threshold defines a selected-claim rule. Assumed
true effects define repeated-study scenarios. Those three roles are not interchangeable.

## Request: `CurveRequest`

`CurveRequest` is declared `total=False`, so every key is statically optional. At runtime,
`lower` and `upper` are required. Unknown mapping keys are ignored by `compute_curves`.

### Observed and presentation request fields

| Field | Declared type | Runtime default / nullability | Scale or units | Ownership and meaning |
|---|---|---|---|---|
| `effect_type` | `str` | `"odds_ratio"` | Registry key | Observed/shared. Selects effect family, transformation, and default null. |
| `estimate` | `float \| None` | `None` | Natural input scale | Observed. Optional validation input; curves remain anchored to the CI midpoint. |
| `lower` | `float` | No usable default; omission raises `ValidationError` | Natural input scale | Observed. Lower reported 95% CI bound. |
| `upper` | `float` | No usable default; omission raises `ValidationError` | Natural input scale | Observed. Upper reported 95% CI bound. |
| `null_value` | `float` | Omission applies effect default (`0` additive, `1` ratio) | Natural input scale | Observed/shared reference null. |
| `thresholds` | `list[float]` | Omission/`None` becomes `[]` | Natural input scale | Observed reference thresholds/MCIDs; also added as design scenarios if design is enabled. They do not define the design claim rule. |
| `display_range_lower` | `float \| None` | `None`; both bounds required together | Natural input scale | Presentation only. Lower plotted/exported observed x-grid bound. |
| `display_range_upper` | `float \| None` | `None`; both bounds required together | Natural input scale | Presentation only. Upper plotted/exported observed x-grid bound. |
| `display_natural_axis` | `bool` | `True` | Boolean | Presentation. For ratio effects, chooses natural versus log-working display values. |
| `grid_points` | `int` | `801`; minimum 101; even values become next odd integer | Count | Shared grid length for observed and enabled design arrays. |
| `show_cutoffs` | `bool` | `True` | Boolean | Presentation metadata controlling compatibility guide/cutoff display. |

### Repeated-study design request fields

| Field | Declared type | Runtime default / nullability | Scale or units | Ownership and meaning |
|---|---|---|---|---|
| `design_enabled` | `bool` | `False` | Boolean | Design. When false, response `design` is `null` and other design fields do not alter observed results. |
| `design_alpha` | `float` | `0.05`; explicit `None` also becomes `0.05` | Probability | Design selected-claim alpha. Must be finite and strictly between 0 and 1. |
| `design_selection_rule` | `str` | `"two_sided_p_lt_alpha"` | Rule key | Design. One of the six frozen selected-claim rules. |
| `design_claim_direction` | `str` | `"positive"` | `"positive"` or `"negative"` | Design. Direction for directional/threshold rules; forced by the two one-sided rule keys. |
| `design_claim_threshold` | `float \| None` | `None`; required by threshold rules | Natural input scale | Design rule threshold/MCID. Distinct from observed `thresholds`. |
| `design_information_multiplier` | `float` | `1.0` | Positive fold ratio | Design. Sets `design_se = current_se / sqrt(multiplier)` and never changes observed reconstruction. |
| `design_precision_target_effect` | `float \| None` | `None` | Natural input scale | Design. Assumed true effect for inverse-precision target rows. |
| `design_target_power` | `float \| None` | If a target effect exists, omitted value becomes `0.80`; otherwise unused | Probability | Design minimum selected-claim probability target. |
| `design_max_type_s` | `float \| None` | `None` | Probability | Design maximum conditional wrong-sign probability. |
| `design_max_type_m` | `float \| None` | `None` | Fold ratio greater than 1 | Design maximum expected selected magnitude exaggeration. |
| `design_true_effects` | `list[float]` | Omission/`None` becomes `[]` | Natural input scale | Design custom assumed-truth scenarios. |
| `design_plausible_range_lower` | `float \| None` | `None`; both bounds required together | Natural input scale | Design presentation metadata only; does not change the computational grid. |
| `design_plausible_range_upper` | `float \| None` | `None`; both bounds required together | Natural input scale | Design presentation metadata only; does not change the computational grid. |

The supported selection-rule keys are:

```text
two_sided_p_lt_alpha
one_sided_positive_p_lt_alpha
one_sided_negative_p_lt_alpha
ci_excludes_null_in_beneficial_direction
estimate_exceeds_mcid_and_p_lt_alpha
ci_excludes_mcid
```

## Response: `CurveResponse`

### Top level

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `meta` | `MetaPayload` | No | Mixed metadata | Observed reconstruction and presentation metadata. |
| `summary` | `SummaryPayload` | No | Mixed | Observed-evidence scalar summaries. |
| `warnings` | `list[str]` | No | Text | Observed/global validation and finite-display warnings; empty when none. |
| `grid` | `GridPayload` | No | Mixed arrays | Observed-evidence grid. |
| `design` | `DesignPayload \| None` | Yes | Mixed | Repeated-study design block; exactly `null` when disabled. |

### `meta.effect_spec`

`effect_spec` is statically typed as `dict[str, object]`, but runtime emits this fixed
shape:

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `key` | `str` | No | Registry key | Shared effect key. |
| `label` | `str` | No | Text | Human-readable effect name. |
| `family` | `"additive" \| "ratio"` | No | Category | Determines identity versus log behavior. |
| `working_scale` | `"identity" \| "log"` | No | Category | Computational scale. |
| `default_null` | `float` | No | Natural input scale | Registry default null. |
| `positive_only` | `bool` | No | Boolean | Whether natural-scale effect values must be positive. |

The frozen registry contains ratio effects `odds_ratio`, `risk_ratio`, `hazard_ratio`,
`incidence_rate_ratio`, and `ratio_of_means`, all with log working scale and null 1.
It contains additive effects `mean_difference`, `risk_difference`, `rate_difference`, and
`regression_coefficient`, all with identity working scale and null 0.

### `meta`

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `effect_spec` | `dict[str, object]` | No | See above | Observed/shared effect metadata. |
| `display_axis_scale` | `str` | No | `"natural"` or `"working"` | Presentation scale used by observed grids/summaries and design grid/scenario `*_display` values. Config/precision fields that preserve raw natural input are identified below. |
| `estimate_source` | `"inferred_from_ci" \| "provided_validated"` | No | Category | Whether a point estimate was omitted or supplied and validated. The numerical reconstruction is CI-midpoint anchored in both cases. |
| `default_null_applied` | `bool` | No | Boolean | Whether the null was omitted and the registry default used. |
| `grid_points` | `int` | No | Count | Actual odd array length after normalization. |
| `show_cutoffs` | `bool` | No | Boolean | Echoed compatibility-guide presentation flag. |
| `se_method` | `str` | No | Category | CI-midpoint SE-detail method label, ordinarily `ci_width` in this adapter; the internal result type also permits `mean_side_se`. |
| `relative_asymmetry` | `float` | No | Dimensionless ratio | Relative lower/upper side-SE disagreement using the provided estimate when present, otherwise the midpoint. |
| `thresholds_display` | `list[float]` | No | Display scale | Observed reference thresholds in input order. |
| `thresholds_working` | `list[float]` | No | Working scale | Same thresholds after transformation. |
| `display_range_active` | `bool` | No | Boolean | Whether explicit display bounds replaced the default grid range. |
| `display_range_display` | `list[float] \| None` | Yes | Display scale, two endpoints | Active plotted/exported x-range, else `null`. |
| `display_range_working` | `list[float] \| None` | Yes | Working scale, two endpoints | Same active range on the computational scale, else `null`. |
| `threshold_support_summaries` | `list[ThresholdSupportPayload]` | No | Mixed | One observed support row per reference threshold; empty when no thresholds. |
| `s_minus_2_interval` | `SMinus2IntervalPayload` | No | Mixed | Fixed Wald S−2 support interval. |

### `meta.threshold_support_summaries[]`

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `threshold_display` | `float` | No | Display scale | Reference threshold. |
| `threshold_working` | `float` | No | Working scale | Transformed reference threshold. |
| `relative_likelihood` | `float` | No | Normalized ratio `[0, 1]` | Wald relative likelihood at the threshold versus the estimate. |
| `log_relative_likelihood` | `float` | No | Natural-log support | Log normalized relative likelihood at the threshold. |
| `likelihood_ratio_mle_to_threshold` | `float \| None` | Yes | Fold ratio | Estimate-to-threshold support ratio; `null` if exponentiation would overflow. |
| `log_likelihood_ratio_mle_to_threshold` | `float` | No | Natural-log ratio | Log estimate-to-threshold support ratio. |
| `likelihood_ratio_threshold_to_null` | `float \| None` | Yes | Fold ratio | Threshold-to-null support ratio; `null` if unavailable or overflowing. |
| `log_likelihood_ratio_threshold_to_null` | `float \| None` | Yes | Natural-log ratio | `null` when the extreme null comparison cannot be represented. |
| `direction_from_estimate` | `str` | No | Category | `below_estimate`, `at_estimate`, or `above_estimate` using frozen numeric closeness. |
| `direction_from_null` | `str` | No | Category | `below_null`, `at_null`, or `above_null`. |

### `meta.s_minus_2_interval`

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `support_cutoff` | `float` | No | Log support | Fixed `-2`. |
| `relative_likelihood_cutoff` | `float` | No | Normalized ratio | Fixed `exp(-2)`. |
| `likelihood_ratio_mle_to_bound` | `float` | No | Fold ratio | Fixed `exp(2)`. |
| `range_display` | `list[float]` | No | Display scale, two endpoints | S−2 endpoints, finite-clipped with warning if necessary. |
| `range_working` | `list[float]` | No | Working scale, two endpoints | `estimate_working ± 2 * working_scale_se`, finite-clipped with warning if necessary. |

### `summary`

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `estimate_display` | `float` | No | Display scale | CI-implied midpoint; geometric midpoint for ratio natural display. |
| `estimate_working` | `float` | No | Working scale | CI-implied Wald estimate. |
| `ci_display` | `list[float]` | No | Display scale, two endpoints | Reported 95% CI represented on the active display scale. |
| `ci_working` | `list[float]` | No | Working scale, two endpoints | Reported 95% CI after transformation. |
| `null_display` | `float` | No | Display scale | Null on the active display scale. |
| `null_working` | `float` | No | Working scale | Null after transformation. |
| `working_scale_se` | `float` | No | Working-scale effect units | Reconstructed Wald SE. |
| `null_relative_likelihood` | `float` | No | Normalized ratio `[0, 1]` | Wald relative likelihood at the null. May underflow to zero. |
| `log_null_relative_likelihood` | `float \| None` | Yes | Natural-log support | Log relative likelihood at the null; `null` only at unrepresentable extreme distance. |
| `likelihood_ratio_mle_to_null` | `float \| None` | Yes | Fold ratio | Estimate-to-null support ratio; `null` on exponentiation overflow/unavailability. |
| `log_likelihood_ratio_mle_to_null` | `float \| None` | Yes | Natural-log ratio | Retained when finite even if the ordinary ratio overflows. |
| `two_sided_wald_p_value` | `float` | No | Probability | Compatibility at the null. |
| `null_z_value` | `float \| None` | Yes | Standardized, dimensionless | Signed null distance; `null` at unrepresentable extreme distance. |
| `critical_effect_markers_display` | `list[float]` | No | Display scale, two values | Legacy paired 80% z-sum benchmark around the null. |
| `critical_effect_markers_working` | `list[float]` | No | Working scale, two values | Same legacy paired benchmark on the computational scale. |
| `critical_effect_distance_working` | `float` | No | Working-scale effect units | `(Z975 + Z80) * working_scale_se`; not a generalized exact power solution. |

### `grid`

All six arrays have length `meta.grid_points` and share row alignment.

| Field | Type | Nullable elements | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `effect_display` | `list[float]` | No | Display scale | Candidate observed effects shown/exported. |
| `effect_working` | `list[float]` | No | Working scale | Same candidate effects on the computational scale. |
| `z` | `list[float]` | No | Standardized, dimensionless | `(effect_working - estimate_working) / working_scale_se`. |
| `compatibility` | `list[float]` | No | Probability | Two-sided Wald p-value/compatibility function. |
| `relative_likelihood` | `list[float]` | No | Normalized ratio `[0, 1]` | Wald relative likelihood, peak 1 at the estimate. |
| `log_relative_likelihood` | `list[float]` | No | Natural-log support | `-0.5 * z**2`. |

### `design.config`

Every field in this and the following design tables belongs to repeated-study design,
except where an observed value is explicitly carried in as precision context.

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `enabled` | `bool` | No | Boolean | Always `true` inside a present design block. |
| `alpha` | `float` | No | Probability | Selected-claim alpha. |
| `selection_rule` | `DesignSelectionRule` | No | Rule key | Active frozen rule. |
| `selection_rule_label` | `str` | No | Text | Human-readable rule label. |
| `claim_direction` | `"positive" \| "negative"` | No | Category | Active claim direction. |
| `claim_threshold_display` | `float \| None` | Yes | Natural input scale | Rule threshold as entered; unlike grid `*_display` fields, it is not converted when a working-scale axis is active. |
| `claim_threshold_working` | `float \| None` | Yes | Working scale | Transformed rule threshold. |
| `se_working` | `float` | No | Working-scale effect units | Alias of `design_se_working` in the frozen contract. |
| `current_se_working` | `float` | No | Working-scale effect units | Observed CI-implied SE carried into the design scenario. |
| `design_se_working` | `float` | No | Working-scale effect units | Hypothetical repeated-study SE after information scaling. |
| `information_multiplier` | `float` | No | Fold ratio | `current_se_working**2 / design_se_working**2`. |
| `current_ci_width_working` | `float` | No | Working-scale effect units | `2 * Z975 * current_se_working`. |
| `approx_design_ci_width_working` | `float` | No | Working-scale effect units | `2 * Z975 * design_se_working`. |
| `null_working` | `float` | No | Working scale | Design null. |
| `estimate_working` | `float` | No | Working scale | CI-implied observed estimate used for retrospective observed-exaggeration calculations; it is not an assumed truth by default. |
| `near_null_delta` | `float` | No | Standardized, dimensionless | Frozen tolerance `1e-12` for undefined Type S/M ratios. |
| `type_m_scale_note` | `str` | No | Text | States additive versus log-ratio Type M interpretation. |
| `plausible_range_display` | `list[float] \| None` | Yes | Natural input scale, two endpoints | Optional design-only shading/metadata range as entered; unlike grid `*_display` fields, it is not converted when a working-scale axis is active. |
| `plausible_range_working` | `list[float] \| None` | Yes | Working scale, two endpoints | Transformed plausible range. |

### `design.grid`

These arrays align by index with the observed `grid`, but their x-values are assumed true
effects rather than candidates evaluated against observed evidence.

| Field | Type | Nullable elements | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `true_effect_display` | `list[float]` | No | Display scale | Candidate assumed true effects. |
| `true_effect_working` | `list[float]` | No | Working scale | Same assumed truths on the computational scale. |
| `delta` | `list[float]` | No | Standardized, dimensionless | `(true_effect_working - null_working) / design_se_working`. |
| `power` | `list[float]` | No | Probability | Selected-claim probability; legacy field name `power` applies even when a rule is not conventionally described as power. |
| `type_s` | `list[float \| None]` | Yes | Probability | Conditional wrong-sign probability; `null` at/near null or when undefined. |
| `type_m` | `list[float \| None]` | Yes | Working-scale fold ratio | Conditional expected selected magnitude divided by true magnitude; `null` at/near null or when undefined. |
| `expected_selected_abs_z` | `list[float \| None]` | Yes | Standardized magnitude | Expected absolute selected future Z; `null` when selection probability is zero. |
| `observed_exaggeration` | `list[float \| None]` | Yes | Working-scale fold ratio | Retrospective observed-to-assumed-true magnitude ratio; distinct from Type M and `null` at/near null. |

### `design.scenarios[]`

Scenario rows are deduplicated on the working scale. Construction precedence is null,
CI-implied estimate, observed thresholds, then custom true effects.

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `label` | `str` | No | Text | Display label. |
| `source` | `str` | No | Category | `null`, `ci_implied_estimate`, `threshold`, or `custom_true_effect`. |
| `true_effect_display` | `float` | No | Display scale | Assumed true effect. |
| `true_effect_working` | `float` | No | Working scale | Transformed assumed truth. |
| `delta` | `float` | No | Standardized, dimensionless | Assumed true effect distance from the null. |
| `power` | `float` | No | Probability | Selected-claim probability. |
| `type_s` | `float \| None` | Yes | Probability | Conditional wrong-sign probability. |
| `type_m` | `float \| None` | Yes | Working-scale fold ratio | Conditional magnitude exaggeration. |
| `observed_exaggeration` | `float \| None` | Yes | Working-scale fold ratio | Retrospective observed exaggeration, not Type M. |
| `note` | `str \| None` | Yes | Text | Null/optimistic-scenario qualification when applicable. |

### `design.precision_targets[]`

Rows appear in stable requested order: `Power`, `Maximum Type S`, then `Maximum Type M`.
An infeasible row remains present with nullable result fields and an explanatory note.

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `target` | `str` | No | Category | Target label. |
| `requested_value` | `float` | No | Probability or fold ratio | Requested threshold, interpreted by `target`. |
| `target_effect_display` | `float` | No | Natural input scale | Assumed true effect as entered; unlike grid `*_display` fields, it is not converted when a working-scale axis is active. |
| `target_effect_working` | `float` | No | Working scale | Transformed target truth. |
| `required_se` | `float \| None` | Yes | Working-scale effect units | Required SE, or `null` if no finite meaningful solution. |
| `required_information_multiplier` | `float \| None` | Yes | Fold ratio | `(current_se / required_se)**2`, or `null`. |
| `approx_95_ci_width_working` | `float \| None` | Yes | Working-scale effect units | `2 * Z975 * required_se`, or `null`. |
| `achieved_power` | `float \| None` | Yes | Probability | Selected-claim probability at solved SE. |
| `achieved_type_s` | `float \| None` | Yes | Probability | Type S at solved SE. |
| `achieved_type_m` | `float \| None` | Yes | Working-scale fold ratio | Type M at solved SE. |
| `note` | `str` | No | Text | Current-sufficient, solver, or no-solution explanation. |

### `design`

| Field | Type | Nullable | Scale or units | Ownership and meaning |
|---|---|---:|---|---|
| `config` | `DesignConfigPayload` | No | Mixed | Rule, scale, and precision assumptions. |
| `grid` | `DesignGridPayload` | No | Mixed arrays | Forward operating characteristics over assumed truths. |
| `scenarios` | `list[DesignScenarioPayload]` | No | Mixed rows | Named assumed-truth rows. |
| `precision_targets` | `list[DesignPrecisionTargetPayload]` | No | Mixed rows | Per-target inverse-precision results; empty without a target effect. |
| `warnings` | `list[str]` | No | Text | Conditioning, scale, display-only range, information, and infeasibility notes. |

## Key-order contract

Python and current JSON serialization preserve insertion order. The frozen implementation
emits the following orders:

```text
CurveResponse:
  meta, summary, warnings, grid, design

meta:
  effect_spec, display_axis_scale, estimate_source, default_null_applied,
  grid_points, show_cutoffs, se_method, relative_asymmetry,
  thresholds_display, thresholds_working, display_range_active,
  display_range_display, display_range_working,
  threshold_support_summaries, s_minus_2_interval

meta.effect_spec:
  key, label, family, working_scale, default_null, positive_only

meta.threshold_support_summaries[]:
  threshold_display, threshold_working, relative_likelihood,
  log_relative_likelihood, likelihood_ratio_mle_to_threshold,
  log_likelihood_ratio_mle_to_threshold, likelihood_ratio_threshold_to_null,
  log_likelihood_ratio_threshold_to_null, direction_from_estimate,
  direction_from_null

meta.s_minus_2_interval:
  support_cutoff, relative_likelihood_cutoff, likelihood_ratio_mle_to_bound,
  range_display, range_working

summary:
  estimate_display, estimate_working, ci_display, ci_working, null_display,
  null_working, working_scale_se, null_relative_likelihood,
  log_null_relative_likelihood, likelihood_ratio_mle_to_null,
  log_likelihood_ratio_mle_to_null, two_sided_wald_p_value, null_z_value,
  critical_effect_markers_display, critical_effect_markers_working,
  critical_effect_distance_working

grid:
  effect_display, effect_working, z, compatibility, relative_likelihood,
  log_relative_likelihood

design:
  config, grid, scenarios, precision_targets, warnings

design.config:
  enabled, alpha, selection_rule, selection_rule_label, claim_direction,
  claim_threshold_display, claim_threshold_working, se_working,
  current_se_working, design_se_working, information_multiplier,
  current_ci_width_working, approx_design_ci_width_working, null_working,
  estimate_working, near_null_delta, type_m_scale_note,
  plausible_range_display, plausible_range_working

design.grid:
  true_effect_display, true_effect_working, delta, power, type_s, type_m,
  expected_selected_abs_z, observed_exaggeration

design.scenarios[]:
  label, source, true_effect_display, true_effect_working, delta, power,
  type_s, type_m, observed_exaggeration, note

design.precision_targets[]:
  target, requested_value, target_effect_display, target_effect_working,
  required_se, required_information_multiplier, approx_95_ci_width_working,
  achieved_power, achieved_type_s, achieved_type_m, note
```

`tests/integration/test_contract_response.py` directly asserts the six-key `grid` order.
The golden comparator additionally checks every recorded response-object order, including
every repeated threshold, scenario, and precision row. The observed grid order is mirrored
by the CSV columns, although the CSV builder names its headers explicitly rather than
iterating object keys. Browser consumers otherwise access response values by name.

The browser CSV schema is a separate ordered export contract:

```text
Observed:
  effect_display, effect_working, z, compatibility,
  relative_likelihood, log_relative_likelihood

Design-enabled additions:
  design_selection_rule, design_claim_direction,
  design_information_multiplier, design_claim_threshold_working,
  design_delta_if_true, design_power_if_true, design_type_s_if_true,
  design_type_m_if_true, design_expected_selected_abs_z_if_true,
  design_observed_exaggeration_if_true
```

The browser E2E tests parse downloaded CSV headers and compare them exactly with the
observed-only and design-enabled schema fixtures.

## Validation and failure behavior

- Invalid scientific or contract inputs raise `confcurve.core.ValidationError`.
- Ratio natural-scale effects, nulls, thresholds, and ranges must be positive.
- Lower/upper pairs must be finite, complete, and strictly ordered.
- The provided estimate is validated against, but does not replace, the CI midpoint.
- Explicit observed display range changes only the grid shown/exported; summaries remain
  based on the reported CI.
- Design information scaling changes only design SE and outputs.
- Type S, Type M, and observed exaggeration are `null` at or near the null.
- Overflow-prone likelihood ratios become `null` while finite log-domain results are
  retained where possible.
- `tests/integration/test_contract_response.py` and
  `tests/integration/test_design_contract.py` exercise strict JSON, ordinary and extreme
  nullability, array alignment, scenario construction, precision rows, and disabled
  design behavior.
