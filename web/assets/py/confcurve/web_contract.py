from __future__ import annotations

from typing import Any

import numpy as np

from .core import (
    LOG_MAX_FLOAT,
    MAX_FLOAT,
    ValidationError,
    asymmetry_warning,
    build_grid,
    confidence_curve,
    critical_effect_distance,
    critical_effect_markers,
    estimate_se_details,
    from_working_scale,
    log_relative_likelihood,
    max_safe_grid_span,
    relative_likelihood,
    summaries,
    to_working_scale,
    validate_inputs,
)
from .models import CurveRequest, CurveResponse


def _float_list(values: float | np.ndarray) -> list[float]:
    return [float(value) for value in np.asarray(values, dtype=float).tolist()]


def _safe_display_values(
    effect_type: str,
    working_scale: str,
    working_values: float | np.ndarray,
) -> tuple[np.ndarray, bool]:
    working_array = np.asarray(working_values, dtype=float)
    if working_scale != "log":
        return np.asarray(from_working_scale(effect_type, working_array), dtype=float), False

    clipped_mask = working_array >= LOG_MAX_FLOAT
    safe_working = np.minimum(working_array, LOG_MAX_FLOAT)
    display_values = np.asarray(from_working_scale(effect_type, safe_working), dtype=float)
    if np.any(clipped_mask):
        display_values = display_values.copy()
        display_values[clipped_mask] = MAX_FLOAT
    return display_values, bool(np.any(clipped_mask))


def _display_range_exclusion_warnings(
    display_range_working: tuple[float, float] | None,
    *,
    theta_hat: float,
    lower_working: float,
    upper_working: float,
    null_working: float,
    thresholds_working: list[float],
    critical_markers_working: tuple[float, float],
) -> list[str]:
    if display_range_working is None:
        return []

    range_lower, range_upper = display_range_working

    def outside_range(value: float) -> bool:
        return value < range_lower or value > range_upper

    warnings: list[str] = []
    if outside_range(theta_hat):
        warnings.append("The chosen display range excludes the point estimate.")
    if outside_range(lower_working):
        warnings.append("The chosen display range excludes the lower 95% CI bound.")
    if outside_range(upper_working):
        warnings.append("The chosen display range excludes the upper 95% CI bound.")
    if outside_range(null_working):
        warnings.append("The chosen display range excludes the null value.")
    if any(outside_range(value) for value in thresholds_working):
        warnings.append("The chosen display range excludes one or more clinical thresholds.")
    if any(outside_range(value) for value in critical_markers_working):
        warnings.append("The chosen display range excludes one or more critical-effect markers.")
    return warnings


def compute_curves(payload: CurveRequest | dict[str, Any]) -> CurveResponse:
    """Compute a JSON-serializable response for the browser app."""

    validated = validate_inputs(
        effect_type=str(payload.get("effect_type", "odds_ratio")),
        estimate=payload.get("estimate"),
        lower=payload.get("lower"),
        upper=payload.get("upper"),
        null_value=payload.get("null_value"),
        thresholds=payload.get("thresholds"),
        display_range_lower=payload.get("display_range_lower"),
        display_range_upper=payload.get("display_range_upper"),
        display_natural_axis=bool(payload.get("display_natural_axis", True)),
        grid_points=int(payload.get("grid_points", 801)),
        show_cutoffs=bool(payload.get("show_cutoffs", True)),
    )

    effect_type = validated.effect_spec.key
    theta_hat = float(to_working_scale(effect_type, validated.estimate))
    lower_working = float(to_working_scale(effect_type, validated.lower))
    upper_working = float(to_working_scale(effect_type, validated.upper))
    null_working = float(to_working_scale(effect_type, validated.null_value))
    thresholds_working = _float_list(to_working_scale(effect_type, validated.thresholds))

    se_info = estimate_se_details(theta_hat=theta_hat, lower=lower_working, upper=upper_working)
    critical_distance_working = critical_effect_distance(se_info.se)
    critical_markers_working = critical_effect_markers(null_working, se=se_info.se)
    safe_span = None
    if validated.display_range_working is None:
        natural_axis_upper_bound = LOG_MAX_FLOAT if validated.display_natural_axis else None
        safe_span = max_safe_grid_span(
            theta_hat=theta_hat,
            se=se_info.se,
            natural_axis_upper_bound=natural_axis_upper_bound,
        )
        grid_working = build_grid(
            theta_hat=theta_hat,
            se=se_info.se,
            n=validated.grid_points,
            include_values=(null_working, *thresholds_working, *critical_markers_working),
            max_span=safe_span,
        )
    else:
        range_lower_working, range_upper_working = validated.display_range_working
        grid_working = np.linspace(
            range_lower_working,
            range_upper_working,
            num=validated.grid_points,
            dtype=float,
        )
        if not np.isfinite(grid_working).all():
            raise ValidationError("Plausible display range must produce a finite x-grid.")
    z_values = (grid_working - theta_hat) / se_info.se
    compatibility = confidence_curve(grid_working, theta_hat=theta_hat, se=se_info.se)
    rel_likelihood = relative_likelihood(grid_working, theta_hat=theta_hat, se=se_info.se)
    log_rel_likelihood = log_relative_likelihood(grid_working, theta_hat=theta_hat, se=se_info.se)
    if validated.display_range_working is not None and (
        not np.isfinite(z_values).all() or not np.isfinite(log_rel_likelihood).all()
    ):
        raise ValidationError(
            "Plausible display range is too far from the CI-derived estimate to plot "
            "with finite floating-point precision."
        )

    display_axis_scale = "natural" if validated.display_natural_axis else "working"
    natural_axis_clipped = False
    if validated.display_natural_axis:
        grid_display, natural_axis_clipped = _safe_display_values(
            effect_type,
            validated.effect_spec.working_scale,
            grid_working,
        )
        estimate_display = validated.estimate
        ci_display = [validated.lower, validated.upper]
        null_display = validated.null_value
        critical_markers_display, critical_markers_clipped = _safe_display_values(
            effect_type,
            validated.effect_spec.working_scale,
            np.asarray(critical_markers_working, dtype=float),
        )
        natural_axis_clipped = natural_axis_clipped or critical_markers_clipped
    else:
        grid_display = grid_working
        estimate_display = theta_hat
        ci_display = [lower_working, upper_working]
        null_display = null_working
        critical_markers_display = np.asarray(critical_markers_working, dtype=float)

    warning_messages = list(validated.warnings)
    if safe_span is not None and any(
        value is not None and abs(value - theta_hat) > safe_span
        for value in (null_working, *thresholds_working, *critical_markers_working)
    ):
        warning_messages.append(
            "Grid expansion was truncated to keep the plotted payload within finite floating-point "
            "range. Very extreme null, threshold, or critical-effect values may fall "
            "outside the plotted x-axis."
        )
    if safe_span == 0.0:
        warning_messages.append(
            "The estimate sits at the finite floating-point boundary on the working scale, "
            "so the plotted x-grid collapses to the estimate."
        )
    warning_messages.extend(
        _display_range_exclusion_warnings(
            validated.display_range_working,
            theta_hat=theta_hat,
            lower_working=lower_working,
            upper_working=upper_working,
            null_working=null_working,
            thresholds_working=thresholds_working,
            critical_markers_working=critical_markers_working,
        )
    )
    if natural_axis_clipped:
        warning_messages.append(
            "Natural-axis x-values were clipped at the largest finite floating-point value. "
            "Working-scale calculations are unchanged."
        )
    observed_estimate = (
        validated.estimate if validated.provided_estimate is None else validated.provided_estimate
    )
    observed_estimate_working = float(to_working_scale(effect_type, observed_estimate))
    observed_estimate_info = estimate_se_details(
        theta_hat=observed_estimate_working,
        lower=lower_working,
        upper=upper_working,
    )
    asymmetry_message = asymmetry_warning(
        validated.effect_spec, observed_estimate_info.relative_asymmetry
    )
    if asymmetry_message is not None:
        warning_messages.append(asymmetry_message)

    null_summary = summaries(theta_hat=theta_hat, se=se_info.se, null_value=null_working)
    if null_summary["log_null_relative_likelihood"] is None:
        warning_messages.append(
            "The null value is too far from the estimate to summarize with finite floating-point "
            "precision. Null likelihood summaries are reported as overflow."
        )
    threshold_display = (
        [float(value) for value in validated.thresholds]
        if validated.display_natural_axis
        else thresholds_working
    )

    return {
        "meta": {
            "effect_spec": {
                "key": validated.effect_spec.key,
                "label": validated.effect_spec.label,
                "family": validated.effect_spec.family,
                "working_scale": validated.effect_spec.working_scale,
                "default_null": validated.effect_spec.default_null,
                "positive_only": validated.effect_spec.positive_only,
            },
            "display_axis_scale": display_axis_scale,
            "estimate_source": validated.estimate_source,
            "default_null_applied": validated.default_null_applied,
            "grid_points": len(grid_working),
            "show_cutoffs": validated.show_cutoffs,
            "se_method": se_info.method,
            "relative_asymmetry": observed_estimate_info.relative_asymmetry,
            "thresholds_display": threshold_display,
            "thresholds_working": thresholds_working,
            "display_range_active": validated.display_range_working is not None,
            "display_range_display": (
                None
                if validated.display_range_working is None
                else [float(grid_display[0]), float(grid_display[-1])]
            ),
            "display_range_working": (
                None
                if validated.display_range_working is None
                else [float(grid_working[0]), float(grid_working[-1])]
            ),
        },
        "summary": {
            "estimate_display": float(estimate_display),
            "estimate_working": theta_hat,
            "ci_display": [float(value) for value in ci_display],
            "ci_working": [lower_working, upper_working],
            "null_display": float(null_display),
            "null_working": null_working,
            "working_scale_se": se_info.se,
            "null_relative_likelihood": null_summary["null_relative_likelihood"],
            "log_null_relative_likelihood": null_summary["log_null_relative_likelihood"],
            "likelihood_ratio_mle_to_null": null_summary["likelihood_ratio_mle_to_null"],
            "log_likelihood_ratio_mle_to_null": null_summary["log_likelihood_ratio_mle_to_null"],
            "two_sided_wald_p_value": null_summary["two_sided_wald_p_value"],
            "null_z_value": null_summary["null_z_value"],
            "critical_effect_markers_display": _float_list(critical_markers_display),
            "critical_effect_markers_working": [float(value) for value in critical_markers_working],
            "critical_effect_distance_working": critical_distance_working,
        },
        "warnings": warning_messages,
        "grid": {
            "effect_display": _float_list(grid_display),
            "effect_working": _float_list(grid_working),
            "z": _float_list(z_values),
            "compatibility": _float_list(compatibility),
            "relative_likelihood": _float_list(rel_likelihood),
            "log_relative_likelihood": _float_list(log_rel_likelihood),
        },
    }
