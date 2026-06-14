from __future__ import annotations

import math
from collections.abc import Callable

import pytest
from scipy.stats import norm

from confcurve.core import ValidationError
from confcurve.design import (
    design_metrics_for_true_effects,
    precision_target_results,
    selection_rule_spec,
    solve_required_delta_for_power,
    solve_required_delta_for_type_m,
    solve_required_delta_for_type_s,
    solve_required_precision,
)


def metric_for_delta(delta: float, *, alpha: float = 0.05):
    return design_metrics_for_true_effects(
        [delta],
        null_working=0.0,
        se=1.0,
        estimate_working=2.0,
        alpha=alpha,
    )[0]


def test_power_at_null_matches_alpha() -> None:
    metric = metric_for_delta(0.0, alpha=0.05)

    assert metric.power == pytest.approx(0.05)
    assert metric.type_s is None
    assert metric.type_m is None
    assert metric.observed_exaggeration is None
    assert metric.expected_selected_abs_z is not None


def test_power_type_s_and_type_m_are_symmetric() -> None:
    positive = metric_for_delta(1.5)
    negative = metric_for_delta(-1.5)

    assert positive.power == pytest.approx(negative.power)
    assert positive.type_s == pytest.approx(negative.type_s)
    assert positive.type_m == pytest.approx(negative.type_m)
    assert positive.expected_selected_abs_z == pytest.approx(negative.expected_selected_abs_z)


def test_type_s_uses_wrong_sign_tail() -> None:
    alpha = 0.05
    critical_z = norm.ppf(1.0 - (alpha / 2.0))
    positive = metric_for_delta(1.0, alpha=alpha)
    negative = metric_for_delta(-1.0, alpha=alpha)

    positive_lower_tail = norm.cdf(-critical_z - 1.0)
    positive_upper_tail = norm.sf(critical_z - 1.0)
    negative_lower_tail = norm.cdf(-critical_z + 1.0)
    negative_upper_tail = norm.sf(critical_z + 1.0)

    assert positive.type_s == pytest.approx(
        positive_lower_tail / (positive_lower_tail + positive_upper_tail)
    )
    assert negative.type_s == pytest.approx(
        negative_upper_tail / (negative_lower_tail + negative_upper_tail)
    )


def test_one_sided_positive_selection_rule_matches_normal_tail() -> None:
    alpha = 0.05
    delta = 0.7
    critical_z = norm.isf(alpha)

    [metric] = design_metrics_for_true_effects(
        [delta],
        null_working=0.0,
        se=1.0,
        alpha=alpha,
        selection_rule="one_sided_positive_p_lt_alpha",
    )
    [wrong_direction_metric] = design_metrics_for_true_effects(
        [-delta],
        null_working=0.0,
        se=1.0,
        alpha=alpha,
        selection_rule="one_sided_positive_p_lt_alpha",
    )

    assert metric.power == pytest.approx(norm.sf(critical_z - delta))
    assert metric.type_s == pytest.approx(0.0)
    assert wrong_direction_metric.type_s == pytest.approx(1.0)


def test_directional_ci_rule_uses_two_sided_ci_tail_in_claim_direction() -> None:
    alpha = 0.05
    critical_z = norm.isf(alpha / 2.0)

    [positive] = design_metrics_for_true_effects(
        [1.0],
        null_working=0.0,
        se=1.0,
        alpha=alpha,
        selection_rule="ci_excludes_null_in_beneficial_direction",
        claim_direction="positive",
    )
    [negative] = design_metrics_for_true_effects(
        [-1.0],
        null_working=0.0,
        se=1.0,
        alpha=alpha,
        selection_rule="ci_excludes_null_in_beneficial_direction",
        claim_direction="negative",
    )

    assert positive.power == pytest.approx(norm.sf(critical_z - 1.0))
    assert negative.power == pytest.approx(norm.cdf(-critical_z + 1.0))
    assert positive.type_s == pytest.approx(0.0)
    assert negative.type_s == pytest.approx(0.0)


def test_threshold_selection_rules_match_exact_tail_boundaries() -> None:
    alpha = 0.05
    critical_z = norm.isf(alpha / 2.0)

    [estimate_exceeds] = design_metrics_for_true_effects(
        [3.0],
        null_working=0.0,
        se=1.0,
        alpha=alpha,
        selection_rule="estimate_exceeds_mcid_and_p_lt_alpha",
        claim_direction="positive",
        threshold_working=2.5,
    )
    [ci_excludes] = design_metrics_for_true_effects(
        [5.0],
        null_working=0.0,
        se=1.0,
        alpha=alpha,
        selection_rule="ci_excludes_mcid",
        claim_direction="positive",
        threshold_working=2.5,
    )

    assert estimate_exceeds.power == pytest.approx(norm.sf(2.5 - 3.0))
    assert ci_excludes.power == pytest.approx(norm.sf((2.5 + critical_z) - 5.0))


def test_selected_alpha_ci_rule_labels_are_alpha_neutral() -> None:
    labels = [
        selection_rule_spec(
            selection_rule="ci_excludes_null_in_beneficial_direction",
            alpha=0.01,
            null_working=0.0,
            se=1.0,
            claim_direction="positive",
        ).label,
        selection_rule_spec(
            selection_rule="ci_excludes_mcid",
            alpha=0.01,
            null_working=0.0,
            se=1.0,
            claim_direction="positive",
            threshold_working=0.2,
        ).label,
    ]

    assert labels == [
        "CI at selected alpha excludes the null in the selected claim direction",
        "CI at selected alpha excludes the claim threshold",
    ]
    assert all("95%" not in label for label in labels)


def test_large_true_effect_has_low_type_s_and_little_expected_exaggeration() -> None:
    metric = metric_for_delta(8.0)

    assert metric.power > 0.99
    assert metric.type_s is not None and metric.type_s < 1e-20
    assert metric.type_m == pytest.approx(1.0, rel=0.02)


def test_near_null_values_return_none_for_undefined_ratios() -> None:
    [metric] = design_metrics_for_true_effects(
        [1e-13],
        null_working=0.0,
        se=1.0,
        estimate_working=2.0,
        near_null_delta=1e-12,
    )

    assert metric.type_s is None
    assert metric.type_m is None
    assert metric.observed_exaggeration is None


def test_near_null_delta_uses_coerced_public_api_value() -> None:
    [metric] = design_metrics_for_true_effects(  # type: ignore[arg-type]
        [0.5],
        null_working=0.0,
        se=1.0,
        estimate_working=1.0,
        near_null_delta="1e-12",
    )

    assert metric.type_m is not None


def test_observed_exaggeration_uses_working_scale_distance_from_null() -> None:
    [metric] = design_metrics_for_true_effects(
        [0.5],
        null_working=0.0,
        se=0.25,
        estimate_working=1.0,
    )

    assert metric.observed_exaggeration == pytest.approx(2.0)


def test_expected_selected_abs_z_matches_exact_formula() -> None:
    delta = 1.25
    alpha = 0.01
    critical_z = norm.ppf(1.0 - (alpha / 2.0))
    metric = metric_for_delta(delta, alpha=alpha)

    upper_tail = norm.sf(critical_z - delta)
    lower_tail = norm.cdf(-critical_z - delta)
    numerator = (
        delta * (upper_tail - lower_tail)
        + norm.pdf(critical_z - delta)
        + norm.pdf(-critical_z - delta)
    )

    assert metric.expected_selected_abs_z == pytest.approx(numerator / metric.power)
    assert metric.type_m == pytest.approx(metric.expected_selected_abs_z / abs(delta))


def test_tiny_alpha_uses_survival_quantile_without_dividing_by_zero() -> None:
    [metric] = design_metrics_for_true_effects(
        [1.0],
        null_working=0.0,
        se=1.0,
        alpha=1e-20,
    )

    assert metric.power > 0
    assert metric.type_s is not None
    assert metric.type_m is not None


def test_too_small_alpha_raises_validation_error() -> None:
    with pytest.raises(ValidationError, match="too small"):
        design_metrics_for_true_effects([1.0], null_working=0.0, se=1.0, alpha=1e-320)


def test_required_delta_solvers_hit_requested_targets() -> None:
    alpha = 0.05
    power_delta = solve_required_delta_for_power(alpha, 0.8)
    type_s_delta = solve_required_delta_for_type_s(alpha, 0.01)
    type_m_delta = solve_required_delta_for_type_m(alpha, 1.25)

    assert metric_for_delta(power_delta, alpha=alpha).power == pytest.approx(0.8)
    assert metric_for_delta(type_s_delta, alpha=alpha).type_s == pytest.approx(0.01)
    assert metric_for_delta(type_m_delta, alpha=alpha).type_m == pytest.approx(1.25)


def test_required_precision_power_target_tightens_se_when_current_power_is_low() -> None:
    [result] = precision_target_results(
        0.5,
        null_working=0.0,
        current_se=0.5,
        target_power=0.8,
    )

    assert result.target == "Power"
    assert result.required_se is not None and result.required_se < 0.5
    assert (
        result.required_information_multiplier is not None
        and result.required_information_multiplier > 1.0
    )
    assert result.achieved_power == pytest.approx(0.8)


def test_stricter_type_m_precision_target_requires_more_information() -> None:
    [looser] = precision_target_results(
        0.5,
        null_working=0.0,
        current_se=0.5,
        max_type_m=1.5,
    )
    [stricter] = precision_target_results(
        0.5,
        null_working=0.0,
        current_se=0.5,
        max_type_m=1.25,
    )

    assert looser.required_information_multiplier is not None
    assert stricter.required_information_multiplier is not None
    assert stricter.required_information_multiplier > looser.required_information_multiplier


def test_near_null_precision_target_returns_no_finite_solution() -> None:
    [result] = precision_target_results(
        0.0,
        null_working=0.0,
        current_se=0.5,
        target_power=0.8,
    )

    assert result.required_se is None
    assert result.required_information_multiplier is None
    assert "near the null" in result.note


def test_solve_required_precision_returns_strictest_finite_target() -> None:
    results = precision_target_results(
        0.5,
        null_working=0.0,
        current_se=0.5,
        target_power=0.8,
        max_type_m=1.25,
    )
    aggregate = solve_required_precision(
        0.5,
        null_working=0.0,
        current_se=0.5,
        target_power=0.8,
        max_type_m=1.25,
    )
    finite_required_se = [
        result.required_se for result in results if result.required_se is not None
    ]

    assert aggregate["required_se"] == pytest.approx(min(finite_required_se))
    assert aggregate["required_information_multiplier"] == pytest.approx(
        max(
            result.required_information_multiplier
            for result in results
            if result.required_information_multiplier is not None
        )
    )


def test_solve_required_precision_returns_none_when_any_requested_target_is_infeasible() -> None:
    per_target = precision_target_results(
        0.5,
        null_working=0.0,
        current_se=1.0,
        selection_rule="ci_excludes_mcid",
        claim_direction="positive",
        threshold_working=1.0,
        target_power=0.8,
        max_type_s=0.5,
    )
    aggregate = solve_required_precision(
        0.5,
        null_working=0.0,
        current_se=1.0,
        selection_rule="ci_excludes_mcid",
        claim_direction="positive",
        threshold_working=1.0,
        target_power=0.8,
        max_type_s=0.5,
    )

    assert [result.required_se is None for result in per_target] == [True, False]
    assert all(value is None for value in aggregate.values())


def test_solve_required_precision_returns_none_when_no_targets_are_requested() -> None:
    aggregate = solve_required_precision(0.5, null_working=0.0, current_se=0.5)

    assert all(value is None for value in aggregate.values())


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"se": 0.0}, "standard error"),
        ({"alpha": 0.0}, "alpha"),
        ({"alpha": 1.0}, "alpha"),
        ({"near_null_delta": -1.0}, "near-null"),
        ({"selection_rule": "one_sided"}, "selection rule"),
        ({"claim_direction": "sideways"}, "claim direction"),
        (
            {
                "selection_rule": "estimate_exceeds_mcid_and_p_lt_alpha",
                "claim_direction": "positive",
            },
            "threshold",
        ),
        (
            {
                "selection_rule": "ci_excludes_mcid",
                "claim_direction": "positive",
                "threshold_working": -0.2,
            },
            "above the null",
        ),
    ],
)
def test_invalid_design_inputs_raise_validation_errors(
    kwargs: dict[str, object], message: str
) -> None:
    base_kwargs = {
        "null_working": 0.0,
        "se": 1.0,
        "alpha": 0.05,
        "near_null_delta": 1e-12,
    }

    with pytest.raises(ValidationError, match=message):
        design_metrics_for_true_effects([0.5], **{**base_kwargs, **kwargs})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: design_metrics_for_true_effects(["abc"], null_working=0.0, se=1.0),
            "true effects",
        ),
        (
            lambda: design_metrics_for_true_effects([0.5], null_working=0.0, se="abc"),  # type: ignore[arg-type]
            "standard error",
        ),
        (
            lambda: design_metrics_for_true_effects([0.5], null_working=0.0, se=1.0, alpha="abc"),  # type: ignore[arg-type]
            "alpha",
        ),
        (
            lambda: solve_required_delta_for_power(0.05, "abc"),  # type: ignore[arg-type]
            "Target power",
        ),
        (
            lambda: precision_target_results(  # type: ignore[arg-type]
                "abc",
                null_working=0.0,
                current_se=0.5,
                target_power=0.8,
            ),
            "precision target effect",
        ),
        (
            lambda: precision_target_results(  # type: ignore[arg-type]
                0.5,
                null_working=0.0,
                current_se="abc",
                target_power=0.8,
            ),
            "standard error",
        ),
        (
            lambda: precision_target_results(  # type: ignore[arg-type]
                0.5,
                null_working=0.0,
                current_se=0.5,
                target_power="abc",
            ),
            "Target power",
        ),
    ],
)
def test_malformed_public_design_api_inputs_raise_validation_error(
    call: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        call()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"target_power": 1.0}, "Target power"),
        ({"max_type_s": 0.0}, "Maximum Type S"),
        ({"max_type_m": 1.0}, "Maximum Type M"),
        ({"current_se": 0.0, "target_power": 0.8}, "standard error"),
    ],
)
def test_invalid_precision_targets_raise_validation_errors(
    kwargs: dict[str, object], message: str
) -> None:
    base_kwargs = {
        "true_effect_working": 0.5,
        "null_working": 0.0,
        "current_se": 0.5,
    }
    base_kwargs.update(kwargs)

    with pytest.raises(ValidationError, match=message):
        precision_target_results(**base_kwargs)  # type: ignore[arg-type]


def test_nonfinite_design_inputs_raise_validation_errors() -> None:
    with pytest.raises(ValidationError, match="true effects"):
        design_metrics_for_true_effects([math.inf], null_working=0.0, se=1.0)

    with pytest.raises(ValidationError, match="null value"):
        design_metrics_for_true_effects([1.0], null_working=math.nan, se=1.0)

    with pytest.raises(ValidationError, match="estimate"):
        design_metrics_for_true_effects([1.0], null_working=0.0, se=1.0, estimate_working=math.inf)
