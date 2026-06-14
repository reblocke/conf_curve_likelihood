from __future__ import annotations

import json
import math

import pytest

from confcurve.core import ValidationError
from confcurve.web_contract import compute_curves


def test_design_block_is_null_when_design_is_disabled() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 401,
        }
    )

    assert response["design"] is None
    json.dumps(response, allow_nan=False)


def test_design_enabled_response_is_grid_aligned_and_json_safe() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "thresholds": [0.2],
            "design_enabled": True,
            "design_alpha": 0.05,
            "design_true_effects": [0.1, 0.3],
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    design = payload["design"]
    assert design["config"]["enabled"] is True
    assert design["config"]["selection_rule"] == "two_sided_p_lt_alpha"
    assert design["config"]["selection_rule_label"] == "Two-sided p < alpha against the null"
    assert design["config"]["alpha"] == pytest.approx(0.05)
    assert design["config"]["information_multiplier"] == pytest.approx(1.0)
    assert design["config"]["current_se_working"] == pytest.approx(
        design["config"]["design_se_working"]
    )
    assert design["grid"]["true_effect_display"] == pytest.approx(payload["grid"]["effect_display"])
    assert len(design["grid"]["power"]) == len(payload["grid"]["effect_display"])
    assert any(scenario["source"] == "null" for scenario in design["scenarios"])
    assert any(scenario["source"] == "ci_implied_estimate" for scenario in design["scenarios"])
    assert any(scenario["source"] == "threshold" for scenario in design["scenarios"])
    assert any(scenario["source"] == "custom_true_effect" for scenario in design["scenarios"])
    assert design["precision_targets"] == []


def test_design_enabled_response_supports_tiny_alpha_when_json_safe() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "design_enabled": True,
            "design_alpha": 1e-20,
            "design_true_effects": [0.3],
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    assert payload["design"]["config"]["alpha"] == pytest.approx(1e-20)
    assert all(value >= 0 for value in payload["design"]["grid"]["power"])


def test_design_ratio_true_effects_are_converted_to_log_working_scale() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "design_enabled": True,
            "design_true_effects": [1.5],
            "grid_points": 401,
        }
    )

    design = response["design"]
    assert design is not None
    custom = next(
        scenario for scenario in design["scenarios"] if scenario["source"] == "custom_true_effect"
    )
    assert custom["true_effect_display"] == pytest.approx(1.5)
    assert custom["true_effect_working"] == pytest.approx(math.log(1.5))
    assert "log working scale" in " ".join(design["warnings"])


def test_design_ratio_claim_threshold_is_converted_to_log_working_scale() -> None:
    response = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "design_enabled": True,
            "design_selection_rule": "ci_excludes_mcid",
            "design_claim_direction": "positive",
            "design_claim_threshold": 1.25,
            "grid_points": 401,
        }
    )

    design = response["design"]
    assert design is not None
    assert design["config"]["selection_rule"] == "ci_excludes_mcid"
    assert design["config"]["claim_direction"] == "positive"
    assert design["config"]["claim_threshold_display"] == pytest.approx(1.25)
    assert design["config"]["claim_threshold_working"] == pytest.approx(math.log(1.25))
    json.dumps(response, allow_nan=False)


def test_design_information_multiplier_changes_design_se_not_observed_summary() -> None:
    base_payload = {
        "effect_type": "mean_difference",
        "lower": 0.11,
        "upper": 0.73,
        "design_enabled": True,
        "grid_points": 401,
    }
    current = compute_curves(base_payload)
    scaled = compute_curves({**base_payload, "design_information_multiplier": 4.0})

    assert current["summary"]["working_scale_se"] == pytest.approx(
        scaled["summary"]["working_scale_se"]
    )
    assert current["summary"]["ci_working"] == pytest.approx(scaled["summary"]["ci_working"])
    assert scaled["design"] is not None
    assert scaled["design"]["config"]["information_multiplier"] == pytest.approx(4.0)
    assert scaled["design"]["config"]["design_se_working"] == pytest.approx(
        scaled["summary"]["working_scale_se"] / 2.0
    )
    assert scaled["design"]["grid"]["power"] != current["design"]["grid"]["power"]


def test_design_precision_target_rows_are_json_safe() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "design_enabled": True,
            "design_precision_target_effect": 0.2,
            "design_target_power": 0.8,
            "design_max_type_s": 0.01,
            "design_max_type_m": 1.25,
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    targets = payload["design"]["precision_targets"]
    assert [target["target"] for target in targets] == [
        "Power",
        "Maximum Type S",
        "Maximum Type M",
    ]
    assert all(target["target_effect_display"] == pytest.approx(0.2) for target in targets)
    assert any(target["required_information_multiplier"] is not None for target in targets)


def test_design_scenarios_deduplicate_working_scale_values() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "thresholds": [0.2],
            "design_enabled": True,
            "design_true_effects": [0.2],
            "grid_points": 401,
        }
    )

    design = response["design"]
    assert design is not None
    matching = [
        scenario for scenario in design["scenarios"] if scenario["true_effect_display"] == 0.2
    ]
    assert len(matching) == 1


def test_design_null_scenario_note_is_rule_dependent_for_directional_ci_rule() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "design_enabled": True,
            "design_alpha": 0.05,
            "design_selection_rule": "ci_excludes_null_in_beneficial_direction",
            "design_claim_direction": "positive",
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response, allow_nan=False))
    null_scenario = next(
        scenario for scenario in payload["design"]["scenarios"] if scenario["source"] == "null"
    )
    assert null_scenario["power"] == pytest.approx(0.025)
    assert null_scenario["note"] == (
        "Type S/M undefined at null; selected-claim probability is rule-dependent "
        "and shown in the Power column."
    )
    assert "power equals alpha" not in null_scenario["note"]


@pytest.mark.parametrize(
    "extra_payload",
    [
        {"design_alpha": 0.0},
        {"design_alpha": 1.0},
        {"design_alpha": 1e-320},
        {"design_alpha": "abc"},
        {"design_selection_rule": "unsupported_rule"},
        {"design_plausible_range_lower": 0.1},
        {"design_plausible_range_lower": "abc", "design_plausible_range_upper": 0.3},
        {"design_information_multiplier": 0.0},
        {"design_information_multiplier": "abc"},
        {"design_true_effects": ["abc"]},
        {"design_precision_target_effect": "abc"},
        {"design_precision_target_effect": 0.2, "design_target_power": "abc"},
        {"design_precision_target_effect": 0.2, "design_max_type_s": "abc"},
        {"design_precision_target_effect": 0.2, "design_max_type_m": "abc"},
        {
            "design_selection_rule": "ci_excludes_mcid",
            "design_claim_direction": "positive",
            "design_claim_threshold": -0.2,
        },
        {
            "design_selection_rule": "ci_excludes_mcid",
            "design_claim_direction": "positive",
            "design_claim_threshold": "abc",
        },
        {
            "design_precision_target_effect": 0.2,
            "design_target_power": 1.0,
        },
    ],
)
def test_invalid_design_contract_inputs_raise_when_enabled(
    extra_payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        compute_curves(
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                **extra_payload,
            }
        )


def test_invalid_design_fields_are_ignored_when_design_is_disabled() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "lower": 0.11,
            "upper": 0.73,
            "design_enabled": False,
            "design_alpha": 0.0,
        }
    )

    assert response["design"] is None
