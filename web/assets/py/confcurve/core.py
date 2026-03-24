from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

import numpy as np
from scipy.stats import norm

from .models import DEFAULT_EFFECT_TYPE, EFFECT_SPECS, EffectSpec, EstimateSource

Z975 = float(norm.ppf(0.975))
Z80 = float(norm.ppf(0.80))
DEFAULT_GRID_POINTS = 801
DEFAULT_SPAN_MULTIPLIER = 4.5
GRID_EXPANSION_PADDING_MULTIPLIER = 0.25
ASYMMETRY_RELATIVE_TOLERANCE = 0.02
ESTIMATE_MATCH_RELATIVE_TOLERANCE = 0.02
ESTIMATE_MATCH_ABSOLUTE_TOLERANCE = 1e-12
MAX_FLOAT = float(np.finfo(float).max)
LOG_MAX_FLOAT = float(np.log(np.finfo(float).max))
MAX_FINITE_SPAN = float(np.finfo(float).max / 4.0)
MAX_FINITE_ABS_Z = float(np.sqrt(np.finfo(float).max))


class ValidationError(ValueError):
    """Raised when curve inputs cannot support a Wald reconstruction."""


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


def _to_array(values: float | Sequence[float] | np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)


def _maybe_scalar(
    original: float | Sequence[float] | np.ndarray, values: np.ndarray
) -> float | np.ndarray:
    if np.isscalar(original):
        return float(values.reshape(-1)[0])
    return values


def _require_finite(values: np.ndarray, label: str) -> None:
    if not np.isfinite(values).all():
        raise ValidationError(f"{label} must be finite.")


def to_working_scale(
    effect_type: str,
    values: float | Sequence[float] | np.ndarray,
) -> float | np.ndarray:
    """Convert values to the Wald working scale for the requested effect type."""

    spec = get_effect_spec(effect_type)
    array = _to_array(values)
    _require_finite(array, "Values")

    if spec.working_scale == "log":
        if np.any(array <= 0):
            raise ValidationError(
                f"{spec.label} values must be strictly positive on the natural scale."
            )
        array = np.log(array)

    return _maybe_scalar(values, array)


def from_working_scale(
    effect_type: str,
    values: float | Sequence[float] | np.ndarray,
) -> float | np.ndarray:
    """Transform working-scale values back to the display scale for the effect type."""

    spec = get_effect_spec(effect_type)
    array = _to_array(values)
    _require_finite(array, "Working-scale values")

    if spec.working_scale == "log":
        array = np.exp(array)

    return _maybe_scalar(values, array)


def _coerce_thresholds(thresholds: Sequence[float] | None) -> tuple[float, ...]:
    if thresholds is None:
        return ()
    if isinstance(thresholds, (str, bytes)):
        raise ValidationError("Thresholds must be supplied as numeric values, not a string.")

    values = tuple(float(value) for value in thresholds)
    if any(not isfinite(value) for value in values):
        raise ValidationError("Threshold values must be finite.")
    return values


def validate_inputs(
    effect_type: str = DEFAULT_EFFECT_TYPE,
    estimate: float | int | None = None,
    lower: float | int | None = None,
    upper: float | int | None = None,
    null_value: float | int | None = None,
    thresholds: Sequence[float] | None = None,
    display_natural_axis: bool = True,
    grid_points: int = DEFAULT_GRID_POINTS,
    show_cutoffs: bool = True,
) -> ValidatedInputs:
    """Validate and normalize user inputs for the Wald reconstruction."""

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

    default_null_applied = null_value is None
    normalized_null = float(spec.default_null if null_value is None else null_value)
    if not isfinite(normalized_null):
        raise ValidationError("Null value must be finite.")

    normalized_thresholds = _coerce_thresholds(thresholds)
    warnings: list[str] = []

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

    lower_working = float(to_working_scale(effect_type, lower_value))
    upper_working = float(to_working_scale(effect_type, upper_value))
    estimate_working = lower_working + ((upper_working - lower_working) / 2.0)
    estimate_display = float(from_working_scale(effect_type, estimate_working))
    ci_half_width_working = (upper_working - lower_working) / 2.0
    estimate_match_tolerance = max(
        ESTIMATE_MATCH_ABSOLUTE_TOLERANCE,
        ESTIMATE_MATCH_RELATIVE_TOLERANCE * ci_half_width_working,
    )

    estimate_source: EstimateSource
    if estimate_value is None:
        estimate_source = "inferred_from_ci"
    else:
        provided_estimate_working = float(to_working_scale(effect_type, estimate_value))
        if abs(provided_estimate_working - estimate_working) > estimate_match_tolerance:
            raise ValidationError(
                "Provided estimate is inconsistent with the supplied 95% confidence "
                "interval on the working scale beyond the rounding tolerance."
            )
        estimate_source = "provided_validated"

    if ci_half_width_working <= 0:
        raise ValidationError(
            "The supplied 95% confidence interval must have positive width on the working scale."
        )

    points = int(grid_points)
    if points < 101:
        raise ValidationError("Grid points must be at least 101.")
    if points % 2 == 0:
        points += 1

    return ValidatedInputs(
        effect_spec=spec,
        estimate=estimate_display,
        estimate_source=estimate_source,
        provided_estimate=estimate_value,
        lower=lower_value,
        upper=upper_value,
        null_value=normalized_null,
        thresholds=normalized_thresholds,
        display_natural_axis=bool(display_natural_axis and spec.family == "ratio"),
        grid_points=points,
        show_cutoffs=bool(show_cutoffs),
        default_null_applied=default_null_applied,
        warnings=tuple(warnings),
    )


def critical_effect_distance(se: float) -> float:
    """Return the working-scale critical effect distance for alpha=.05 and power=.80."""

    if se <= 0:
        raise ValidationError("Standard error must be positive.")
    return float((Z975 + Z80) * se)


def critical_effect_markers(null_value: float, se: float) -> tuple[float, float]:
    """Return symmetric critical-effect markers around the null on the working scale."""

    distance = critical_effect_distance(se)
    return (null_value - distance, null_value + distance)


def estimate_se_details(theta_hat: float, lower: float, upper: float) -> StandardErrorEstimate:
    """Reconstruct the working-scale standard error from a symmetric Wald CI."""

    se_width = (upper - lower) / (2.0 * Z975)
    se_lower = (theta_hat - lower) / Z975
    se_upper = (upper - theta_hat) / Z975
    mean_side_se = float(np.mean([se_lower, se_upper]))

    relative_asymmetry = abs(se_upper - se_lower) / max(abs(mean_side_se), np.finfo(float).eps)
    if relative_asymmetry > ASYMMETRY_RELATIVE_TOLERANCE:
        return StandardErrorEstimate(
            se=mean_side_se,
            method="mean_side_se",
            se_lower=se_lower,
            se_upper=se_upper,
            se_width=se_width,
            relative_asymmetry=relative_asymmetry,
        )

    return StandardErrorEstimate(
        se=se_width,
        method="ci_width",
        se_lower=se_lower,
        se_upper=se_upper,
        se_width=se_width,
        relative_asymmetry=relative_asymmetry,
    )


def estimate_se(theta_hat: float, lower: float, upper: float) -> float:
    """Return the reconstructed working-scale standard error."""

    return estimate_se_details(theta_hat, lower, upper).se


def build_grid(
    theta_hat: float,
    se: float,
    span_multiplier: float = DEFAULT_SPAN_MULTIPLIER,
    n: int = DEFAULT_GRID_POINTS,
    include_values: Sequence[float] | None = None,
    max_span: float | None = None,
) -> np.ndarray:
    """Build a symmetric working-scale grid around the point estimate."""

    if se <= 0:
        raise ValidationError("Standard error must be positive.")
    if span_multiplier <= 0:
        raise ValidationError("Span multiplier must be positive.")
    points = int(n)
    if points < 5:
        raise ValidationError("Grid must contain at least 5 points.")
    if points % 2 == 0:
        points += 1

    span = span_multiplier * se
    if include_values is not None:
        values = _to_array(include_values)
        if values.size:
            _require_finite(values, "Included grid values")
            required_span = float(np.max(np.abs(values - theta_hat)))
            if required_span > span:
                span = required_span + (GRID_EXPANSION_PADDING_MULTIPLIER * se)
    if max_span is not None:
        if max_span < 0:
            raise ValidationError("Maximum span must not be negative.")
        span = min(span, max_span)
    if span == 0:
        return np.full(points, theta_hat, dtype=float)

    return np.linspace(theta_hat - span, theta_hat + span, num=points, dtype=float)


def standardized_distance(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Compute the Wald standardized distance from the estimate."""

    values = _to_array(theta)
    if se <= 0:
        raise ValidationError("Standard error must be positive.")
    return (values - theta_hat) / se


def confidence_curve(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Map the standardized distance to the two-sided compatibility scale."""

    z_values = standardized_distance(theta, theta_hat=theta_hat, se=se)
    return 2.0 * norm.sf(np.abs(z_values))


def relative_likelihood(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Map the standardized distance to a normalized Wald relative likelihood."""

    z_values = standardized_distance(theta, theta_hat=theta_hat, se=se)
    return np.exp(-0.5 * np.square(z_values))


def log_relative_likelihood(
    theta: float | np.ndarray,
    theta_hat: float,
    se: float,
) -> np.ndarray:
    """Return the log relative likelihood on the Wald working scale."""

    z_values = standardized_distance(theta, theta_hat=theta_hat, se=se)
    return -0.5 * np.square(z_values)


def max_safe_grid_span(
    theta_hat: float,
    se: float,
    *,
    natural_axis_upper_bound: float | None = None,
) -> float:
    """Return the largest span that keeps grid endpoints and z values finite."""

    z_safe_span = float(MAX_FINITE_ABS_Z * se)
    endpoint_headroom = max(MAX_FLOAT - abs(theta_hat), 0.0)
    span_limit = min(MAX_FINITE_SPAN, z_safe_span, endpoint_headroom)
    if natural_axis_upper_bound is not None and natural_axis_upper_bound > theta_hat:
        span_limit = min(span_limit, natural_axis_upper_bound - theta_hat)
    return max(span_limit, 0.0)


def summaries(theta_hat: float, se: float, null_value: float) -> dict[str, float | None]:
    """Return summary statistics for the null value versus the MLE."""

    null_distance = abs(null_value - theta_hat)
    if null_distance > (MAX_FINITE_ABS_Z * se):
        return {
            "null_relative_likelihood": 0.0,
            "log_null_relative_likelihood": None,
            "likelihood_ratio_mle_to_null": None,
            "log_likelihood_ratio_mle_to_null": None,
            "two_sided_wald_p_value": 0.0,
            "null_z_value": None,
        }

    null_z_value = float(
        standardized_distance(null_value, theta_hat=theta_hat, se=se).reshape(-1)[0]
    )
    log_null_relative_likelihood = float(
        log_relative_likelihood(null_value, theta_hat=theta_hat, se=se).reshape(-1)[0]
    )
    null_relative_likelihood = float(np.exp(log_null_relative_likelihood))
    log_likelihood_ratio_mle_to_null = -log_null_relative_likelihood
    likelihood_ratio_mle_to_null = (
        None
        if log_likelihood_ratio_mle_to_null > LOG_MAX_FLOAT
        else float(np.exp(log_likelihood_ratio_mle_to_null))
    )
    two_sided_wald_p_value = float(2.0 * norm.sf(abs(null_z_value)))

    return {
        "null_relative_likelihood": null_relative_likelihood,
        "log_null_relative_likelihood": log_null_relative_likelihood,
        "likelihood_ratio_mle_to_null": likelihood_ratio_mle_to_null,
        "log_likelihood_ratio_mle_to_null": log_likelihood_ratio_mle_to_null,
        "two_sided_wald_p_value": two_sided_wald_p_value,
        "null_z_value": null_z_value,
    }


def asymmetry_warning(spec: EffectSpec, relative_asymmetry: float) -> str | None:
    if relative_asymmetry <= ASYMMETRY_RELATIVE_TOLERANCE:
        return None

    if spec.family == "ratio":
        return (
            "CI is not symmetric on the log scale; "
            "this may reflect rounding or a non-Wald interval. "
            "The plotted curves are a Wald approximation."
        )
    return (
        "CI is not symmetric on the working scale; "
        "this may reflect rounding or a non-Wald interval. "
        "The plotted curves are a Wald approximation."
    )
