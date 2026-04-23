from __future__ import annotations

import json
import math

import numpy as np
import pytest

from confcurve.core import (
    MAX_FLOAT,
    Z80,
    Z975,
    ValidationError,
    confidence_curve,
    estimate_se,
    relative_likelihood,
)
from confcurve.web_contract import compute_curves


def test_curves_peak_at_the_estimate() -> None:
    theta_hat = 0.42
    se = 0.157

    compatibility = confidence_curve(theta_hat, theta_hat=theta_hat, se=se)
    rel_likelihood = relative_likelihood(theta_hat, theta_hat=theta_hat, se=se)

    assert compatibility.item() == pytest.approx(1.0)
    assert rel_likelihood.item() == pytest.approx(1.0)


def test_confidence_curve_hits_point_oh_five_at_working_scale_bounds() -> None:
    theta_hat = 0.42
    lower = 0.11
    upper = 0.73
    se = estimate_se(theta_hat, lower=lower, upper=upper)

    compatibility = confidence_curve(np.array([lower, upper]), theta_hat=theta_hat, se=se)

    assert compatibility.tolist() == pytest.approx([0.05, 0.05], rel=1e-3, abs=1e-5)


def test_relative_likelihood_matches_wald_value_at_ci_bounds() -> None:
    theta_hat = 0.42
    lower = 0.11
    upper = 0.73
    se = estimate_se(theta_hat, lower=lower, upper=upper)
    expected = math.exp(-(Z975**2) / 2.0)

    rel_likelihood = relative_likelihood(np.array([lower, upper]), theta_hat=theta_hat, se=se)

    assert rel_likelihood.tolist() == pytest.approx([expected, expected], rel=1e-4)


def test_additive_ci_only_payload_infers_midpoint_estimate() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 401,
        }
    )

    assert response["meta"]["estimate_source"] == "inferred_from_ci"
    assert response["summary"]["estimate_display"] == pytest.approx(0.42)
    assert response["summary"]["estimate_working"] == pytest.approx(0.42)


def test_large_opposite_signed_additive_ci_infers_a_finite_midpoint() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": -1e308,
            "upper": 1e308,
            "grid_points": 401,
        }
    )

    assert response["meta"]["estimate_source"] == "inferred_from_ci"
    assert response["summary"]["estimate_display"] == pytest.approx(0.0)
    assert response["summary"]["estimate_working"] == pytest.approx(0.0)
    assert math.isfinite(response["summary"]["working_scale_se"])
    assert all(math.isfinite(value) for value in response["grid"]["effect_display"])
    json.dumps(response, allow_nan=False)


def test_ratio_ci_only_payload_infers_geometric_mean_estimate() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "grid_points": 401,
        }
    )

    expected_estimate = math.sqrt(1.2 * 2.7)
    assert response["meta"]["estimate_source"] == "inferred_from_ci"
    assert response["summary"]["estimate_display"] == pytest.approx(expected_estimate)
    assert response["summary"]["estimate_working"] == pytest.approx(math.log(expected_estimate))


def test_ratio_inputs_match_pre_logged_working_scale_inputs() -> None:
    natural_response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 1.0,
            "display_natural_axis": False,
            "grid_points": 401,
        }
    )
    working_response = compute_curves(
        {
            "effect_type": "regression_coefficient",
            "lower": math.log(1.2),
            "upper": math.log(2.7),
            "null_value": 0.0,
            "display_natural_axis": False,
            "grid_points": 401,
        }
    )

    assert natural_response["grid"]["effect_working"] == pytest.approx(
        working_response["grid"]["effect_working"]
    )
    assert natural_response["grid"]["compatibility"] == pytest.approx(
        working_response["grid"]["compatibility"]
    )
    assert natural_response["grid"]["relative_likelihood"] == pytest.approx(
        working_response["grid"]["relative_likelihood"]
    )


def test_provided_estimate_within_tolerance_is_validated_but_curves_use_ci_midpoint() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "estimate": 0.423,
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 401,
        }
    )

    assert response["meta"]["estimate_source"] == "provided_validated"
    assert response["summary"]["estimate_display"] == pytest.approx(0.42)


def test_provided_estimate_outside_tolerance_raises_a_validation_error() -> None:
    with pytest.raises(
        ValidationError, match="inconsistent with the supplied 95% confidence interval"
    ):
        compute_curves(
            {
                "effect_type": "mean_difference",
                "estimate": 0.5,
                "lower": 0.11,
                "upper": 0.73,
            }
        )


def test_invalid_ratio_inputs_raise_errors() -> None:
    with pytest.raises(ValidationError):
        compute_curves(
            {
                "effect_type": "odds_ratio",
                "lower": 0.0,
                "upper": 2.0,
            }
        )


def test_display_range_requires_both_bounds() -> None:
    with pytest.raises(ValidationError, match="supplied together"):
        compute_curves(
            {
                "effect_type": "odds_ratio",
                "lower": 1.2,
                "upper": 2.7,
                "display_range_lower": 0.9,
            }
        )


def test_display_range_requires_ordered_finite_bounds() -> None:
    with pytest.raises(ValidationError, match="less than"):
        compute_curves(
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "display_range_lower": 0.5,
                "display_range_upper": 0.2,
            }
        )

    with pytest.raises(ValidationError, match="must be finite"):
        compute_curves(
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "display_range_lower": 0.2,
                "display_range_upper": math.inf,
            }
        )


def test_ratio_display_range_requires_positive_bounds() -> None:
    with pytest.raises(ValidationError, match="strictly positive"):
        compute_curves(
            {
                "effect_type": "odds_ratio",
                "lower": 1.2,
                "upper": 2.7,
                "display_range_lower": 0.0,
                "display_range_upper": 1.1,
            }
        )


def test_active_display_range_metadata_and_grid_match_requested_range() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "display_range_lower": 0.9,
            "display_range_upper": 1.1,
            "grid_points": 401,
        }
    )

    assert response["meta"]["display_range_active"] is True
    assert response["meta"]["display_range_display"] == pytest.approx([0.9, 1.1])
    assert response["meta"]["display_range_working"] == pytest.approx(
        [math.log(0.9), math.log(1.1)]
    )
    assert response["grid"]["effect_display"][0] == pytest.approx(0.9)
    assert response["grid"]["effect_display"][-1] == pytest.approx(1.1)
    assert response["grid"]["effect_working"][0] == pytest.approx(math.log(0.9))
    assert response["grid"]["effect_working"][-1] == pytest.approx(math.log(1.1))


def test_default_display_range_metadata_is_inactive() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "grid_points": 401,
        }
    )

    assert response["meta"]["display_range_active"] is False
    assert response["meta"]["display_range_display"] is None
    assert response["meta"]["display_range_working"] is None


def test_display_range_preserves_reconstruction_summaries() -> None:
    baseline = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 1.0,
            "thresholds": [1.25],
            "grid_points": 401,
        }
    )
    constrained = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 1.0,
            "thresholds": [1.25],
            "display_range_lower": 0.9,
            "display_range_upper": 1.1,
            "grid_points": 401,
        }
    )

    for key, expected in baseline["summary"].items():
        observed = constrained["summary"][key]
        if expected is None:
            assert observed is None
        else:
            assert observed == pytest.approx(expected)
    assert constrained["meta"]["estimate_source"] == baseline["meta"]["estimate_source"]
    assert constrained["meta"]["se_method"] == baseline["meta"]["se_method"]
    assert constrained["meta"]["relative_asymmetry"] == pytest.approx(
        baseline["meta"]["relative_asymmetry"]
    )
    for key, expected in baseline["meta"]["s_minus_2_interval"].items():
        observed = constrained["meta"]["s_minus_2_interval"][key]
        if isinstance(expected, list):
            assert observed == pytest.approx(expected)
        else:
            assert observed == pytest.approx(expected)


def test_s_minus_2_interval_matches_wald_support_definition() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "grid_points": 401,
        }
    )

    interval = response["meta"]["s_minus_2_interval"]
    estimate_working = response["summary"]["estimate_working"]
    se = response["summary"]["working_scale_se"]
    expected_working = [estimate_working - 2.0 * se, estimate_working + 2.0 * se]
    expected_display = [math.exp(value) for value in expected_working]

    assert interval["support_cutoff"] == pytest.approx(-2.0)
    assert interval["relative_likelihood_cutoff"] == pytest.approx(math.exp(-2.0))
    assert interval["likelihood_ratio_mle_to_bound"] == pytest.approx(math.exp(2.0))
    assert interval["range_working"] == pytest.approx(expected_working)
    assert interval["range_display"] == pytest.approx(expected_display)


def test_display_range_does_not_auto_expand_to_reference_markers() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 12.0,
            "thresholds": [8.0],
            "display_range_lower": 0.9,
            "display_range_upper": 1.1,
            "grid_points": 401,
        }
    )

    x_values = response["grid"]["effect_display"]
    assert x_values[0] == pytest.approx(0.9)
    assert x_values[-1] == pytest.approx(1.1)
    assert x_values[-1] < 8.0
    assert x_values[-1] < 12.0


def test_display_range_warns_when_key_references_are_excluded() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 12.0,
            "thresholds": [8.0],
            "display_range_lower": 0.9,
            "display_range_upper": 1.1,
            "grid_points": 401,
        }
    )

    messages = "\n".join(response["warnings"])
    assert "excludes the point estimate" in messages
    assert "excludes the lower 95% CI bound" in messages
    assert "excludes the upper 95% CI bound" in messages
    assert "excludes the null value" in messages
    assert "excludes one or more clinical thresholds" in messages
    assert "excludes one or more critical-effect markers" in messages


def test_display_range_rejects_non_finite_grid_payloads() -> None:
    with pytest.raises(ValidationError, match="finite floating-point precision"):
        compute_curves(
            {
                "effect_type": "mean_difference",
                "lower": -1e-320,
                "upper": 1e-320,
                "display_range_lower": -1e308,
                "display_range_upper": 1e308,
                "grid_points": 401,
            }
        )


def test_estimate_within_tolerance_can_still_trigger_asymmetry_warning() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "estimate": 0.425,
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 401,
        }
    )

    assert any("working scale" in message for message in response["warnings"])


def test_even_grid_points_are_normalized_to_an_odd_count() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 400,
        }
    )

    assert response["meta"]["grid_points"] == 401


def test_critical_effect_markers_for_additive_measures_match_expected_distance() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "null_value": 0.0,
            "grid_points": 401,
        }
    )

    expected_distance = (Z975 + Z80) * response["summary"]["working_scale_se"]
    assert response["summary"]["critical_effect_distance_working"] == pytest.approx(
        expected_distance
    )
    assert response["summary"]["critical_effect_markers_working"] == pytest.approx(
        [-expected_distance, expected_distance]
    )
    assert response["summary"]["critical_effect_markers_display"] == pytest.approx(
        [-expected_distance, expected_distance]
    )


def test_critical_effect_markers_for_ratio_measures_back_transform_correctly() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 1.0,
            "display_natural_axis": True,
            "grid_points": 401,
        }
    )

    expected_distance = (Z975 + Z80) * response["summary"]["working_scale_se"]
    assert response["summary"]["critical_effect_markers_working"] == pytest.approx(
        [-expected_distance, expected_distance]
    )
    assert response["summary"]["critical_effect_markers_display"] == pytest.approx(
        [math.exp(-expected_distance), math.exp(expected_distance)]
    )


def test_distant_null_thresholds_and_critical_markers_expand_the_grid_extent() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 12.0,
            "thresholds": [8.0],
            "grid_points": 401,
        }
    )

    x_values = response["grid"]["effect_display"]
    critical_markers = response["summary"]["critical_effect_markers_display"]
    assert x_values[0] < min(*critical_markers, 8.0)
    assert x_values[-1] > max(*critical_markers, 12.0)


def test_threshold_support_summaries_match_wald_likelihood_values() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 1.0,
            "thresholds": [1.25],
            "grid_points": 401,
        }
    )

    threshold_summary = response["meta"]["threshold_support_summaries"][0]
    estimate_working = response["summary"]["estimate_working"]
    se = response["summary"]["working_scale_se"]
    threshold_working = math.log(1.25)
    expected_log_relative_likelihood = -0.5 * ((threshold_working - estimate_working) / se) ** 2
    expected_relative_likelihood = math.exp(expected_log_relative_likelihood)
    expected_threshold_to_null = (
        expected_log_relative_likelihood - response["summary"]["log_null_relative_likelihood"]
    )

    assert threshold_summary["threshold_display"] == pytest.approx(1.25)
    assert threshold_summary["threshold_working"] == pytest.approx(threshold_working)
    assert threshold_summary["log_relative_likelihood"] == pytest.approx(
        expected_log_relative_likelihood
    )
    assert threshold_summary["relative_likelihood"] == pytest.approx(expected_relative_likelihood)
    assert threshold_summary["log_likelihood_ratio_mle_to_threshold"] == pytest.approx(
        -expected_log_relative_likelihood
    )
    assert threshold_summary["likelihood_ratio_mle_to_threshold"] == pytest.approx(
        1.0 / expected_relative_likelihood
    )
    assert threshold_summary["log_likelihood_ratio_threshold_to_null"] == pytest.approx(
        expected_threshold_to_null
    )
    assert threshold_summary["likelihood_ratio_threshold_to_null"] == pytest.approx(
        math.exp(expected_threshold_to_null)
    )
    assert threshold_summary["direction_from_estimate"] == "below_estimate"
    assert threshold_summary["direction_from_null"] == "above_null"


def test_threshold_support_summaries_are_empty_without_thresholds() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "grid_points": 401,
        }
    )

    assert response["meta"]["threshold_support_summaries"] == []


def test_extreme_null_summary_stays_strictly_json_serializable() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": -0.0001,
            "upper": 0.0001,
            "null_value": 100.0,
            "grid_points": 401,
        }
    )

    assert response["summary"]["null_relative_likelihood"] == 0.0
    assert response["summary"]["likelihood_ratio_mle_to_null"] is None
    assert response["summary"]["log_null_relative_likelihood"] is not None
    json.dumps(response, allow_nan=False)


def test_extreme_additive_null_keeps_the_grid_payload_finite() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": -1e-320,
            "upper": 1e-320,
            "null_value": 1e308,
            "grid_points": 401,
        }
    )

    assert all(math.isfinite(value) for value in response["grid"]["effect_display"])
    assert all(math.isfinite(value) for value in response["grid"]["z"])
    assert all(math.isfinite(value) for value in response["grid"]["log_relative_likelihood"])
    assert response["summary"]["log_null_relative_likelihood"] is None
    assert any("finite floating-point range" in message for message in response["warnings"])
    json.dumps(response, allow_nan=False)


def test_extreme_ratio_null_keeps_the_natural_axis_payload_finite() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "null_value": 1.79e308,
            "display_natural_axis": True,
            "grid_points": 401,
        }
    )

    assert all(math.isfinite(value) for value in response["grid"]["effect_display"])
    assert response["grid"]["effect_display"][-1] < float("inf")
    assert response["summary"]["likelihood_ratio_mle_to_null"] is None
    assert response["summary"]["log_likelihood_ratio_mle_to_null"] is not None
    json.dumps(response, allow_nan=False)


def test_large_additive_estimate_keeps_grid_endpoints_finite() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 1.5e308,
            "upper": 1.7e308,
            "grid_points": 401,
        }
    )

    assert all(math.isfinite(value) for value in response["grid"]["effect_display"])
    assert response["grid"]["effect_display"][-1] <= MAX_FLOAT
    assert any("finite floating-point range" in message for message in response["warnings"])
    json.dumps(response, allow_nan=False)


def test_float_max_ratio_interval_returns_a_finite_natural_axis_response() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": MAX_FLOAT / 2.0,
            "upper": MAX_FLOAT,
            "display_natural_axis": True,
            "grid_points": 401,
        }
    )

    assert response["meta"]["estimate_source"] == "inferred_from_ci"
    assert all(math.isfinite(value) for value in response["grid"]["effect_display"])
    assert response["grid"]["effect_display"][-1] == MAX_FLOAT
    assert any("Natural-axis x-values were clipped" in message for message in response["warnings"])
    json.dumps(response, allow_nan=False)
