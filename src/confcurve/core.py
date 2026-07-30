from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

import numpy as np
from wald_inference import (
    ValidationError as ValidationError,
)
from wald_inference import (
    estimate_se_details as _core_estimate_se_details,
)
from wald_inference import legacy as _legacy
from wald_inference import (
    legacy_critical_effect_distance as _core_critical_effect_distance,
)
from wald_inference import (
    legacy_critical_effect_markers as _core_critical_effect_markers,
)
from wald_inference import (
    max_safe_grid_span as _core_max_safe_grid_span,
)
from wald_inference import (
    reconstruct_wald_from_95_ci,
)
from wald_inference import (
    standardized_distance as _core_standardized_distance,
)
from wald_inference.legacy import (
    ASYMMETRY_RELATIVE_TOLERANCE as ASYMMETRY_RELATIVE_TOLERANCE,
)
from wald_inference.legacy import (
    DEFAULT_GRID_POINTS,
    DEFAULT_SPAN_MULTIPLIER,
)
from wald_inference.legacy import (
    ESTIMATE_MATCH_ABSOLUTE_TOLERANCE as ESTIMATE_MATCH_ABSOLUTE_TOLERANCE,
)
from wald_inference.legacy import (
    ESTIMATE_MATCH_RELATIVE_TOLERANCE as ESTIMATE_MATCH_RELATIVE_TOLERANCE,
)
from wald_inference.legacy import (
    GRID_EXPANSION_PADDING_MULTIPLIER as GRID_EXPANSION_PADDING_MULTIPLIER,
)
from wald_inference.legacy import (
    LOG_MAX_FLOAT as LOG_MAX_FLOAT,
)
from wald_inference.legacy import (
    MAX_FINITE_ABS_Z as MAX_FINITE_ABS_Z,
)
from wald_inference.legacy import (
    MAX_FINITE_SPAN as MAX_FINITE_SPAN,
)
from wald_inference.legacy import (
    MAX_FLOAT as MAX_FLOAT,
)
from wald_inference.legacy import Z80 as Z80
from wald_inference.legacy import (
    Z975 as Z975,
)
from wald_inference.legacy import (
    asymmetry_warning as _core_asymmetry_warning,
)

from .models import DEFAULT_EFFECT_TYPE, EFFECT_SPECS, EffectSpec, EstimateSource


@dataclass(frozen=True)
class ValidatedInputs:
    effect_spec: EffectSpec
    estimate: float
    estimate_source: EstimateSource
    provided_estimate: float | None
    lower: float
    upper: float
    null_value: float
    thresholds: tuple[float, ...]
    display_range_working: tuple[float, float] | None
    display_natural_axis: bool
    grid_points: int
    show_cutoffs: bool
    default_null_applied: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class StandardErrorEstimate:
    se: float
    method: str
    se_lower: float
    se_upper: float
    se_width: float
    relative_asymmetry: float


def get_effect_spec(effect_type: str) -> EffectSpec:
    try:
        return EFFECT_SPECS[effect_type]
    except KeyError as exc:
        valid = ", ".join(sorted(EFFECT_SPECS))
        raise ValidationError(
            f"Unsupported effect type {effect_type!r}. Expected one of: {valid}."
        ) from exc


def to_working_scale(
    effect_type: str,
    values: float | Sequence[float] | np.ndarray,
) -> float | np.ndarray:
    """Preserve the frozen natural-to-working-scale direct-call contract."""

    return _legacy.to_working_scale(effect_type, values)


def from_working_scale(
    effect_type: str,
    values: float | Sequence[float] | np.ndarray,
) -> float | np.ndarray:
    """Preserve the frozen working-to-natural-scale direct-call contract."""

    return _legacy.from_working_scale(effect_type, values)


def _coerce_thresholds(thresholds: Sequence[float] | None) -> tuple[float, ...]:
    if thresholds is None:
        return ()
    if isinstance(thresholds, (str, bytes)):
        raise ValidationError("Thresholds must be supplied as numeric values, not a string.")

    values = tuple(float(value) for value in thresholds)
    if any(not isfinite(value) for value in values):
        raise ValidationError("Threshold values must be finite.")
    return values


def _coerce_display_range(
    effect_type: str,
    spec: EffectSpec,
    lower: float | int | None,
    upper: float | int | None,
) -> tuple[float, float] | None:
    lower_present = lower is not None
    upper_present = upper is not None
    if not lower_present and not upper_present:
        return None
    if lower_present != upper_present:
        raise ValidationError("Plausible display range lower and upper must be supplied together.")

    lower_value = float(lower)
    upper_value = float(upper)
    for label, value in (
        ("Plausible display range lower", lower_value),
        ("Plausible display range upper", upper_value),
    ):
        if not isfinite(value):
            raise ValidationError(f"{label} must be finite.")

    if spec.positive_only and (lower_value <= 0 or upper_value <= 0):
        raise ValidationError(
            f"{spec.label} plausible display range bounds must be strictly positive "
            "on the natural scale."
        )
    if lower_value >= upper_value:
        raise ValidationError(
            "Plausible display range lower must be less than plausible display range upper."
        )

    lower_working = float(to_working_scale(effect_type, lower_value))
    upper_working = float(to_working_scale(effect_type, upper_value))
    if lower_working >= upper_working:
        raise ValidationError(
            "Plausible display range lower must be less than plausible display range upper "
            "on the working scale."
        )
    try:
        _core_standardized_distance(
            upper_working,
            lower_working,
            1.0,
        )
    except ValidationError as exc:
        raise ValidationError(
            "Plausible display range is too wide to plot with finite floating-point precision."
        ) from exc
    return lower_working, upper_working


def validate_inputs(
    effect_type: str = DEFAULT_EFFECT_TYPE,
    estimate: float | int | None = None,
    lower: float | int | None = None,
    upper: float | int | None = None,
    null_value: float | int | None = None,
    thresholds: Sequence[float] | None = None,
    display_range_lower: float | int | None = None,
    display_range_upper: float | int | None = None,
    display_natural_axis: bool = True,
    grid_points: int = DEFAULT_GRID_POINTS,
    show_cutoffs: bool = True,
) -> ValidatedInputs:
    """Validate app inputs while delegating Wald reconstruction to the released core."""

    spec = get_effect_spec(effect_type)
    if lower is None or upper is None:
        raise ValidationError("Lower and upper confidence limits are required.")

    estimate_value = None if estimate is None else float(estimate)
    lower_value = float(lower)
    upper_value = float(upper)
    for label, value in (
        ("Lower confidence limit", lower_value),
        ("Upper confidence limit", upper_value),
    ):
        if not isfinite(value):
            raise ValidationError(f"{label} must be finite.")
    if estimate_value is not None and not isfinite(estimate_value):
        raise ValidationError("Estimate must be finite.")
    if lower_value >= upper_value:
        raise ValidationError(
            "The lower confidence limit must be less than the upper confidence limit."
        )

    normalized_null = float(spec.default_null if null_value is None else null_value)
    if not isfinite(normalized_null):
        raise ValidationError("Null value must be finite.")

    normalized_thresholds = _coerce_thresholds(thresholds)
    display_range = _coerce_display_range(
        effect_type,
        spec,
        display_range_lower,
        display_range_upper,
    )
    if spec.positive_only:
        positive_values = [
            lower_value,
            upper_value,
            normalized_null,
            *normalized_thresholds,
        ]
        if estimate_value is not None:
            positive_values.append(estimate_value)
        if any(value <= 0 for value in positive_values):
            raise ValidationError(
                f"{spec.label} inputs must be strictly positive on the natural scale."
            )

    reconstruction = reconstruct_wald_from_95_ci(
        effect_type=effect_type,
        estimate=estimate_value,
        lower=lower_value,
        upper=upper_value,
        null_value=None if null_value is None else normalized_null,
    )

    points = int(grid_points)
    if points < 101:
        raise ValidationError("Grid points must be at least 101.")
    if points % 2 == 0:
        points += 1

    return ValidatedInputs(
        effect_spec=spec,
        estimate=reconstruction.estimate_display,
        estimate_source=reconstruction.estimate_source,
        provided_estimate=reconstruction.provided_estimate_display,
        lower=reconstruction.lower_display,
        upper=reconstruction.upper_display,
        null_value=reconstruction.null_display,
        thresholds=normalized_thresholds,
        display_range_working=display_range,
        display_natural_axis=bool(display_natural_axis and spec.family == "ratio"),
        grid_points=points,
        show_cutoffs=bool(show_cutoffs),
        default_null_applied=reconstruction.default_null_applied,
        warnings=(),
    )


def critical_effect_distance(se: float) -> float:
    """Return the preserved alpha=.05/power=.80 legacy benchmark distance."""

    return _core_critical_effect_distance(se)


def critical_effect_markers(null_value: float, se: float) -> tuple[float, float]:
    """Return the preserved symmetric legacy benchmark markers."""

    return _core_critical_effect_markers(null_value, se)


def estimate_se_details(theta_hat: float, lower: float, upper: float) -> StandardErrorEstimate:
    """Adapt the released core SE result to the frozen local dataclass."""

    result = _core_estimate_se_details(theta_hat, lower, upper)
    return StandardErrorEstimate(
        se=result.se,
        method=result.method,
        se_lower=result.se_lower,
        se_upper=result.se_upper,
        se_width=result.se_width,
        relative_asymmetry=result.relative_asymmetry,
    )


def estimate_se(theta_hat: float, lower: float, upper: float) -> float:
    """Preserve the frozen direct-call standard-error contract."""

    return _legacy.estimate_se(theta_hat, lower, upper)


def build_grid(
    theta_hat: float,
    se: float,
    span_multiplier: float = DEFAULT_SPAN_MULTIPLIER,
    n: int = DEFAULT_GRID_POINTS,
    include_values: Sequence[float] | None = None,
    max_span: float | None = None,
) -> np.ndarray:
    """Preserve the frozen direct-call grid contract."""

    return _legacy.build_grid(
        theta_hat,
        se,
        span_multiplier,
        n,
        include_values,
        max_span,
    )


def standardized_distance(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Delegate finite standardized-distance calculation to the released core."""

    return _core_standardized_distance(theta, theta_hat, se)


def confidence_curve(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Preserve the frozen direct-call compatibility-curve contract."""

    return _legacy.confidence_curve(theta, theta_hat, se)


def relative_likelihood(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Preserve the frozen direct-call normalized-likelihood contract."""

    return _legacy.relative_likelihood(theta, theta_hat, se)


def log_relative_likelihood(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Preserve the frozen direct-call log-likelihood contract."""

    return _legacy.log_relative_likelihood(theta, theta_hat, se)


def max_safe_grid_span(
    theta_hat: float,
    se: float,
    *,
    natural_axis_upper_bound: float | None = None,
) -> float:
    """Delegate finite grid-span selection to the released core."""

    return _core_max_safe_grid_span(
        theta_hat,
        se,
        natural_axis_upper_bound=natural_axis_upper_bound,
    )


def summaries(theta_hat: float, se: float, null_value: float) -> dict[str, float | None]:
    """Preserve the frozen direct-call null-summary mapping."""

    return _legacy.summaries(theta_hat, se, null_value)


def asymmetry_warning(spec: EffectSpec, relative_asymmetry: float) -> str | None:
    """Delegate the frozen reconstruction warning threshold and wording."""

    return _core_asymmetry_warning(spec, relative_asymmetry)
