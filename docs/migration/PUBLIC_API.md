# Frozen Public Python API

## Status and authority

This inventory records the package-level compatibility surface at behavior source commit
`f77cd13f0286e933a66c0997af288a0dfa167bd5`. It is descriptive, not a proposed API for
`wald-inference-core`.

The authority for membership and order is `src/confcurve/__init__.py`. Signatures and
return annotations come from the imported objects in `src/confcurve/core.py`,
`src/confcurve/design.py`, `src/confcurve/web_contract.py`, and `src/confcurve/stage.py`.
All 22 names below are compatibility-surface names because they occur in
`confcurve.__all__`; the classification shown for each name is its primary responsibility.

The exact `__all__` order is:

```text
DesignMetric
PrecisionTargetResult
SelectionRuleSpec
Z975
build_grid
compute_curves
confidence_curve
design_metrics_for_true_effects
estimate_se
from_working_scale
log_relative_likelihood
precision_target_results
relative_likelihood
selection_rule_spec
solve_required_delta_for_power
solve_required_delta_for_type_m
solve_required_delta_for_type_s
solve_required_precision
stage_web_python_package
summaries
to_working_scale
validate_inputs
```

The staged-package integration test verifies that `compute_curves` remains in
`confcurve.__all__`, but no current test asserts the complete membership or order. The
list above is nevertheless the frozen adapter inventory for milestone 02; changing it
requires deliberate compatibility review.

## Scale and conditioning conventions

- A **working-scale effect** is identity-scale for additive measures and log-scale for
  ratio measures.
- A **display value** is natural-scale for a ratio measure only when natural-axis display
  is active; otherwise it is the working-scale value. Additive display and working values
  are numerically identical.
- A standardized effect or `delta` is dimensionless.
- Compatibility, selected-claim probability, and Type S are probabilities in `[0, 1]`.
- Relative likelihood is dimensionless and normalized to one at the CI-implied estimate.
- Type M and observed exaggeration are dimensionless fold ratios based on working-scale
  distance from the null.
- Observed functions condition on the reported estimate/95% CI reconstruction. Design
  functions condition on candidate values treated as assumed true effects under a
  repeated-study Wald model.

## Exported data and type definitions

### `DesignMetric`

```python
DesignMetric(
    true_effect_working: float,
    delta: float,
    power: float,
    type_s: float | None,
    type_m: float | None,
    expected_selected_abs_z: float | None,
    observed_exaggeration: float | None,
)
```

- **Owner / class:** `confcurve.design`; frozen data/type definition.
- **Contract:** frozen dataclass for one assumed true working-scale effect. `power` is the
  selected-claim probability under the configured rule. Type S, Type M, and observed
  exaggeration are `None` at or within `near_null_delta` of the null. Expected selected
  absolute Z is `None` when selection probability is zero. Observed exaggeration is also
  `None` when no observed estimate is supplied.
- **Current verification:** `tests/test_design_metrics.py` directly verifies null,
  symmetry, wrong-tail, directional-rule, threshold-rule, near-null, expected-absolute-Z,
  and observed-exaggeration behavior. `tests/integration/test_design_contract.py` verifies
  strict-JSON conversion of the browser representation.

### `PrecisionTargetResult`

```python
PrecisionTargetResult(
    target: str,
    requested_value: float,
    required_se: float | None,
    required_information_multiplier: float | None,
    approx_95_ci_width_working: float | None,
    achieved_power: float | None,
    achieved_type_s: float | None,
    achieved_type_m: float | None,
    note: str,
)
```

- **Owner / class:** `confcurve.design`; frozen data/type definition.
- **Contract:** frozen per-target inverse-precision result. SE and CI width are on the
  working scale; information multiplier and achieved metrics are dimensionless. All
  numerical result fields after `requested_value` may be `None` when no finite meaningful
  solution exists.
- **Current verification:** precision-target, strictest-target, infeasible-target, and
  validation tests in `tests/test_design_metrics.py`; browser row ordering and strict JSON
  in `tests/integration/test_design_contract.py`.

### `SelectionRuleSpec`

```python
SelectionRuleSpec(
    key: SelectionRule,
    label: str,
    alpha: float,
    claim_direction: ClaimDirection,
    threshold_working: float | None,
    threshold_delta: float | None,
    intervals: tuple[tuple[float, float], ...],
)
```

- **Owner / class:** `confcurve.design`; frozen data/type definition.
- **Contract:** selected-claim regions on the future standardized Wald-Z scale. Internal
  interval endpoints may use positive or negative infinity; this object is not itself a
  browser JSON payload. `threshold_delta` is populated only for threshold rules;
  `threshold_working` may still echo a supplied, nonoperative threshold for another rule.
- **Current verification:** all six rule boundaries and labels are exercised in
  `tests/test_design_metrics.py`.

## Exported numerical and validation primitives

### `Z975`

```python
Z975: float  # scipy.stats.norm.ppf(0.975), currently 1.959963984540054
```

- **Owner / class:** `confcurve.core`; numerical constant.
- **Contract:** dimensionless standard-normal 97.5th percentile used for the fixed 95% CI
  reconstruction.
- **Current verification:** CI-bound compatibility/likelihood and legacy critical-marker
  tests in `tests/test_core.py`.

### `to_working_scale` and `from_working_scale`

```python
to_working_scale(
    effect_type: str,
    values: float | Sequence[float] | np.ndarray,
) -> float | np.ndarray

from_working_scale(
    effect_type: str,
    values: float | Sequence[float] | np.ndarray,
) -> float | np.ndarray
```

- **Owner / class:** `confcurve.core`; numerical primitives.
- **Contract:** identity transformation for additive effects and natural-log/exponential
  transformation for ratio effects. Scalar input returns `float`; sequence or array input
  returns `np.ndarray`. Inputs must be finite; ratio inputs to `to_working_scale` must be
  positive.
- **Current verification:** additive/log equivalence and invalid-ratio tests in
  `tests/test_core.py`, plus round-trip and invalid-input properties in
  `tests/test_properties.py`.

### `validate_inputs`

```python
validate_inputs(
    effect_type: str = "odds_ratio",
    estimate: float | int | None = None,
    lower: float | int | None = None,
    upper: float | int | None = None,
    null_value: float | int | None = None,
    thresholds: Sequence[float] | None = None,
    display_range_lower: float | int | None = None,
    display_range_upper: float | int | None = None,
    display_natural_axis: bool = True,
    grid_points: int = 801,
    show_cutoffs: bool = True,
) -> ValidatedInputs
```

- **Owner / class:** `confcurve.core`; validation primitive and compatibility surface.
- **Contract:** validates observed inputs and returns the internal frozen
  `ValidatedInputs` dataclass. Lower and upper 95% CI bounds are functionally required.
  The reconstructed estimate remains the working-scale CI midpoint; a supplied estimate
  is validation input. Display-range bounds must be supplied together. Grid size must be
  at least 101 and is increased by one when even.
- **Current verification:** reconstruction, estimate tolerance, range, positivity,
  finite-value, and grid-normalization tests in `tests/test_core.py` and
  `tests/test_properties.py`.

### `estimate_se`

```python
estimate_se(theta_hat: float, lower: float, upper: float) -> float
```

- **Owner / class:** `confcurve.core`; numerical primitive.
- **Contract:** reconstructs a positive working-scale SE from a nominal 95% Wald interval.
  Inputs are already on the working scale.
- **Current verification:** CI-bound compatibility and likelihood tests in
  `tests/test_core.py`; browser reconstruction tests exercise the asymmetry-aware internal
  detail function used by `compute_curves`.

### `build_grid`

```python
build_grid(
    theta_hat: float,
    se: float,
    span_multiplier: float = 4.5,
    n: int = 801,
    include_values: Sequence[float] | None = None,
    max_span: float | None = None,
) -> np.ndarray
```

- **Owner / class:** `confcurve.core`; numerical/presentation-grid primitive.
- **Contract:** returns an odd-length, symmetric working-scale grid centered on
  `theta_hat`; direct calls require at least five points. `include_values` may expand the
  span, and `max_span` caps it. This grid does not change reconstruction summaries.
- **Current verification:** indirect coverage through grid expansion, display-range,
  finite-endpoint, and odd-grid tests in `tests/test_core.py` and contract array-length
  tests in `tests/integration/test_contract_response.py`.

### `confidence_curve`, `relative_likelihood`, and `log_relative_likelihood`

```python
confidence_curve(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray

relative_likelihood(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray

log_relative_likelihood(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray
```

- **Owner / class:** `confcurve.core`; observed-evidence numerical primitives.
- **Contract:** all inputs are working-scale effects and SE. They compute, respectively,
  `2 * Normal.sf(abs(z))`, `exp(-0.5 * z**2)`, and `-0.5 * z**2`, where
  `z = (theta - theta_hat) / se`. Outputs are dimensionless NumPy results.
- **Current verification:** peaks, CI-bound targets, scale equivalence, symmetry, and
  monotonic-distance properties in `tests/test_core.py` and
  `tests/test_properties.py`; strict browser arrays in
  `tests/integration/test_contract_response.py`.

### `summaries`

```python
summaries(
    theta_hat: float,
    se: float,
    null_value: float,
) -> dict[str, float | None]
```

- **Owner / class:** `confcurve.core`; observed-evidence numerical primitive.
- **Contract:** inputs are working-scale values. The returned keys, in current insertion
  order, are `null_relative_likelihood`, `log_null_relative_likelihood`,
  `likelihood_ratio_mle_to_null`, `log_likelihood_ratio_mle_to_null`,
  `two_sided_wald_p_value`, and `null_z_value`. Exponentiated likelihood ratio is `None`
  on overflow; the log-domain result is retained when finite. At still more extreme
  distances, unavailable log and Z quantities are also `None`.
- **Current verification:** extreme finite behavior in `tests/test_core.py` and inverse
  relative-likelihood properties in `tests/test_properties.py`.

### `selection_rule_spec`

```python
selection_rule_spec(
    *,
    selection_rule: str = "two_sided_p_lt_alpha",
    alpha: float = 0.05,
    null_working: float = 0.0,
    se: float = 1.0,
    claim_direction: str = "positive",
    threshold_working: float | None = None,
) -> SelectionRuleSpec
```

- **Owner / class:** `confcurve.design`; repeated-study numerical/validation primitive.
- **Contract:** validates and translates one of the six frozen rule keys into selected
  future-Z intervals. Null, SE, and optional threshold are working-scale quantities.
  Threshold rules require a threshold on the claimed side of the null.
- **Current verification:** rule-tail, threshold-direction, alpha, label, and malformed
  input tests in `tests/test_design_metrics.py`.

### `design_metrics_for_true_effects`

```python
design_metrics_for_true_effects(
    true_effects_working: Sequence[float] | np.ndarray,
    *,
    null_working: float,
    se: float,
    estimate_working: float | None = None,
    alpha: float = 0.05,
    selection_rule: str = "two_sided_p_lt_alpha",
    claim_direction: str = "positive",
    threshold_working: float | None = None,
    near_null_delta: float = 1e-12,
) -> list[DesignMetric]
```

- **Owner / class:** `confcurve.design`; repeated-study numerical primitive.
- **Contract:** treats every input effect as an assumed truth and returns one
  `DesignMetric` in input order. Effects, null, optional estimate, threshold, and SE are on
  the working scale; `near_null_delta` is a dimensionless standardized-distance
  tolerance.
- **Current verification:** direct scientific and validation tests throughout
  `tests/test_design_metrics.py`; grid/scenario conversion and strict JSON in
  `tests/integration/test_design_contract.py`.

### Required-delta solvers

```python
solve_required_delta_for_power(
    alpha: float,
    target_power: float,
) -> float

solve_required_delta_for_type_m(
    alpha: float,
    max_type_m: float,
) -> float

solve_required_delta_for_type_s(
    alpha: float,
    max_type_s: float,
) -> float
```

- **Owner / class:** `confcurve.design`; repeated-study numerical primitives.
- **Contract:** return nonnegative, dimensionless absolute standardized effects for the
  default two-sided `p < alpha` rule. They are not generalized rule-specific
  detectability APIs. Power and Type S targets must be strictly between zero and one;
  maximum Type M must exceed one.
- **Current verification:** requested-target equality and malformed/invalid target tests
  in `tests/test_design_metrics.py`.

### `precision_target_results`

```python
precision_target_results(
    true_effect_working: float,
    *,
    null_working: float,
    current_se: float,
    alpha: float = 0.05,
    target_power: float | None = None,
    max_type_s: float | None = None,
    max_type_m: float | None = None,
    selection_rule: str = "two_sided_p_lt_alpha",
    claim_direction: str = "positive",
    threshold_working: float | None = None,
    near_null_delta: float = 1e-12,
    z975: float = 1.959963984540054,
) -> list[PrecisionTargetResult]
```

- **Owner / class:** `confcurve.design`; repeated-study inverse-precision primitive.
- **Contract:** returns requested rows in stable `Power`, `Maximum Type S`, `Maximum Type
  M` order, omitting targets not requested. Effect, null, threshold, SE, and approximate
  CI width use the working scale. It returns an empty list when no targets are supplied
  and preserves infeasible targets as rows with nullable results and an explanatory note.
- **Current verification:** precision, ordering, strictness, near-null, infeasibility, and
  invalid-input tests in `tests/test_design_metrics.py`; browser row ordering in
  `tests/integration/test_design_contract.py`.

### `solve_required_precision`

```python
solve_required_precision(
    true_effect_working: float,
    *,
    null_working: float,
    current_se: float,
    alpha: float = 0.05,
    target_power: float | None = None,
    max_type_s: float | None = None,
    max_type_m: float | None = None,
    selection_rule: str = "two_sided_p_lt_alpha",
    claim_direction: str = "positive",
    threshold_working: float | None = None,
    near_null_delta: float = 1e-12,
    z975: float = 1.959963984540054,
) -> dict[str, float | None]
```

- **Owner / class:** `confcurve.design`; repeated-study inverse-precision primitive.
- **Contract:** returns the strictest requested feasible row with keys
  `required_se`, `required_information_multiplier`, `approx_95_ci_width_working`,
  `achieved_power`, `achieved_type_s`, and `achieved_type_m`, in that insertion order. If
  no targets are supplied or any requested target is infeasible, all six values are
  `None`.
- **Current verification:** strictest-target, infeasible-target, and no-target tests in
  `tests/test_design_metrics.py`.

## Browser contract and staging exports

### `compute_curves`

```python
compute_curves(
    payload: CurveRequest | dict[str, Any],
) -> CurveResponse
```

- **Owner / class:** `confcurve.web_contract`; browser contract.
- **Contract:** validates a partial request mapping, computes the observed response and
  optional design block, and is intended to return a strict-JSON-serializable nested
  mapping. The frozen source has one accepted extreme-design counterexample, documented in
  `docs/migration/CURRENT_BEHAVIOR.md`; resolving it is a release gate, not behavior to
  silently normalize in this inventory. This function is the integrated browser adapter,
  not a pure numerical-core API. Its full field, scale, nullability, conditioning, and
  ordering contract is recorded in `docs/migration/CONTRACT_SCHEMA.md`.
- **Current verification:** `tests/integration/test_contract_response.py`,
  `tests/integration/test_design_contract.py`, strict-JSON tests in `tests/test_core.py`,
  and the Playwright suites under `tests/e2e/`.

### `stage_web_python_package`

```python
stage_web_python_package(
    target_dir: Path,
) -> list[Path]
```

- **Owner / class:** `confcurve.stage`; staging/build helper.
- **Contract:** creates the target directory as needed and overwrites the six listed
  package files in fixed `PACKAGE_FILES` order: `__init__.py`, `core.py`, `design.py`,
  `models.py`, `stage.py`, and `web_contract.py`. It returns their target paths. It does
  not remove unlisted stale files.
- **Current verification:** copy equality, committed-stage parity, and top-level staged
  import tests in `tests/integration/test_contract_and_stage.py`.

## Exceptions and non-exported implementation types

Public functions raise `confcurve.core.ValidationError`, a `ValueError` subclass, for
invalid scientific or contract inputs. `ValidationError`, `ValidatedInputs`,
`StandardErrorEstimate`, `EffectSpec`, the request/response `TypedDict`s, and private
finite-value helpers are importable only from their owner modules and are not members of
the frozen package-level `__all__` surface.
