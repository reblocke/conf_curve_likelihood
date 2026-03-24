from __future__ import annotations

from typing import Any

import numpy as np

from .core import (
    LOG_MAX_FLOAT,
    MAX_FLOAT,
    asymmetry_warning,
    build_grid,
    confidence_curve,
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


def _safe_display_grid(
    effect_type: str,
    working_scale: str,
    grid_working: np.ndarray,
) -> tuple[np.ndarray, bool]:
    working_values = np.asarray(grid_working, dtype=float)
    if working_scale != "log":
        return np.asarray(from_working_scale(effect_type, working_values), dtype=float), False

    clipped_mask = working_values >= LOG_MAX_FLOAT
    safe_working = np.minimum(working_values, LOG_MAX_FLOAT)
    display_values = np.asarray(from_working_scale(effect_type, safe_working), dtype=float)
    if np.any(clipped_mask):
        display_values = display_values.copy()
        display_values[clipped_mask] = MAX_FLOAT
    return display_values, bool(np.any(clipped_mask))


def compute_curves(payload: CurveRequest | dict[str, Any]) -> CurveResponse:
    """Compute a JSON-serializable response for the browser app."""

    validated = validate_inputs(
        effect_type=str(payload.get("effect_type", "odds_ratio")),
        estimate=payload.get("estimate"),
        lower=payload.get("lower"),
        upper=payload.get("upper"),
        null_value=payload.get("null_value"),
        thresholds=payload.get("thresholds"),
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
        include_values=(null_working, *thresholds_working),
        max_span=safe_span,
    )
    z_values = (grid_working - theta_hat) / se_info.se
    compatibility = confidence_curve(grid_working, theta_hat=theta_hat, se=se_info.se)
    rel_likelihood = relative_likelihood(grid_working, theta_hat=theta_hat, se=se_info.se)
    log_rel_likelihood = log_relative_likelihood(grid_working, theta_hat=theta_hat, se=se_info.se)

    display_axis_scale = "natural" if validated.display_natural_axis else "working"
    natural_axis_clipped = False
    if validated.display_natural_axis:
        grid_display, natural_axis_clipped = _safe_display_grid(
            effect_type,
            validated.effect_spec.working_scale,
            grid_working,
        )
        estimate_display = validated.estimate
        ci_display = [validated.lower, validated.upper]
        null_display = validated.null_value
    else:
        grid_display = grid_working
        estimate_display = theta_hat
        ci_display = [lower_working, upper_working]
        null_display = null_working

    warning_messages = list(validated.warnings)
    if any(
        value is not None and abs(value - theta_hat) > safe_span
        for value in (null_working, *thresholds_working)
    ):
        warning_messages.append(
            "Grid expansion was truncated to keep the plotted payload within finite floating-point "
            "range. Very extreme null or threshold values may fall outside the plotted x-axis."
        )
    if safe_span == 0.0:
        warning_messages.append(
            "The estimate sits at the finite floating-point boundary on the working scale, "
            "so the plotted x-grid collapses to the estimate."
        )
    if natural_axis_clipped:
        warning_messages.append(
            "Natural-axis x-values were clipped at the largest finite floating-point value. "
            "Working-scale calculations are unchanged."
        )
    asymmetry_message = asymmetry_warning(validated.effect_spec, se_info.relative_asymmetry)
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
            "default_null_applied": validated.default_null_applied,
            "grid_points": len(grid_working),
            "show_cutoffs": validated.show_cutoffs,
            "se_method": se_info.method,
            "relative_asymmetry": se_info.relative_asymmetry,
            "thresholds_display": threshold_display,
            "thresholds_working": thresholds_working,
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
