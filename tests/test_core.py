from __future__ import annotations

import math

import numpy as np
import pytest

from confcurve.core import Z975, ValidationError, confidence_curve, estimate_se, relative_likelihood
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


def test_ratio_inputs_match_pre_logged_working_scale_inputs() -> None:
    natural_response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "estimate": 1.8,
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
            "estimate": math.log(1.8),
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


def test_invalid_ratio_inputs_raise_errors() -> None:
    with pytest.raises(ValidationError):
        compute_curves(
            {
                "effect_type": "odds_ratio",
                "estimate": 1.2,
                "lower": 0.0,
                "upper": 2.0,
            }
        )


def test_asymmetric_intervals_trigger_warning() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "estimate": 2.0,
            "lower": 1.1,
            "upper": 3.9,
            "grid_points": 401,
        }
    )

    assert any("log scale" in message for message in response["warnings"])


def test_even_grid_points_are_normalized_to_an_odd_count() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "estimate": 0.42,
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 400,
        }
    )

    assert response["meta"]["grid_points"] == 401
