from __future__ import annotations

import json

import pytest

from confcurve.core import MAX_FLOAT
from confcurve.web_contract import compute_curves


def test_compute_curves_response_is_json_serializable() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    assert payload["meta"]["grid_points"] == 401
    assert payload["meta"]["estimate_source"] == "inferred_from_ci"
    assert payload["meta"]["display_range_active"] is False
    assert payload["meta"]["display_range_display"] is None
    assert payload["meta"]["display_range_working"] is None
    assert payload["summary"]["estimate_display"] == 0.42
    assert payload["summary"]["null_display"] == 0.0
    assert payload["summary"]["critical_effect_distance_working"] > 0
    assert list(payload["grid"]) == [
        "effect_display",
        "effect_working",
        "z",
        "compatibility",
        "relative_likelihood",
        "log_relative_likelihood",
    ]
    assert len(payload["grid"]["effect_display"]) == 401


def test_active_display_range_response_metadata_is_json_serializable() -> None:
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

    payload = json.loads(json.dumps(response, allow_nan=False))
    assert payload["meta"]["display_range_active"] is True
    assert payload["meta"]["display_range_display"] == pytest.approx([0.9, 1.1])
    assert payload["meta"]["display_range_working"][0] < payload["meta"]["display_range_working"][1]
    assert payload["grid"]["effect_display"][0] == pytest.approx(0.9)
    assert payload["grid"]["effect_display"][-1] == pytest.approx(1.1)


def test_provided_estimate_sets_provided_validated_meta_flag() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "estimate": 0.423,
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    assert payload["meta"]["estimate_source"] == "provided_validated"
    assert payload["summary"]["estimate_display"] == 0.42


def test_extreme_responses_remain_valid_json_for_the_browser_bridge() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": -0.0001,
            "upper": 0.0001,
            "null_value": 100.0,
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    assert payload["summary"]["likelihood_ratio_mle_to_null"] is None
    assert payload["summary"]["log_null_relative_likelihood"] is not None


def test_extreme_ratio_display_responses_remain_valid_json_for_the_browser_bridge() -> None:
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

    payload = json.loads(json.dumps(response, allow_nan=False))
    assert payload["summary"]["likelihood_ratio_mle_to_null"] is None
    assert payload["summary"]["log_likelihood_ratio_mle_to_null"] is not None
    assert payload["grid"]["effect_display"][-1] < float("inf")


def test_float_max_boundary_responses_remain_valid_json_for_the_browser_bridge() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": MAX_FLOAT / 2.0,
            "upper": MAX_FLOAT,
            "display_natural_axis": True,
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    assert payload["meta"]["estimate_source"] == "inferred_from_ci"
    assert payload["grid"]["effect_display"][-1] == MAX_FLOAT
    assert any("Natural-axis x-values were clipped" in message for message in payload["warnings"])
