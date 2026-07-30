from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypeAlias

import numpy as np
from wald_inference import (
    DEFAULT_CLAIM_DIRECTION as CORE_DEFAULT_CLAIM_DIRECTION,
)
from wald_inference import (
    DEFAULT_NEAR_NULL_DELTA,
)
from wald_inference import (
    DEFAULT_SELECTION_RULE as CORE_DEFAULT_SELECTION_RULE,
)
from wald_inference import (
    design_metrics_for_true_effects as _core_design_metrics_for_true_effects,
)
from wald_inference import (
    precision_target_results as _core_precision_target_results,
)
from wald_inference import (
    selection_rule_spec as _core_selection_rule_spec,
)
from wald_inference import (
    solve_required_delta_for_power as _core_solve_required_delta_for_power,
)
from wald_inference import (
    solve_required_delta_for_type_m as _core_solve_required_delta_for_type_m,
)
from wald_inference import (
    solve_required_delta_for_type_s as _core_solve_required_delta_for_type_s,
)
from wald_inference import (
    solve_required_precision as _core_solve_required_precision,
)
from wald_inference.legacy import (
    DEFAULT_SOLVER_TOLERANCE as DEFAULT_SOLVER_TOLERANCE,
)
from wald_inference.legacy import (
    MAX_INFORMATION_MULTIPLIER as MAX_INFORMATION_MULTIPLIER,
)

SelectionRule: TypeAlias = Literal[
    "two_sided_p_lt_alpha",
    "one_sided_positive_p_lt_alpha",
    "one_sided_negative_p_lt_alpha",
    "ci_excludes_null_in_beneficial_direction",
    "estimate_exceeds_mcid_and_p_lt_alpha",
    "ci_excludes_mcid",
]
ClaimDirection: TypeAlias = Literal["positive", "negative"]
DEFAULT_SELECTION_RULE: SelectionRule = CORE_DEFAULT_SELECTION_RULE
DEFAULT_CLAIM_DIRECTION: ClaimDirection = CORE_DEFAULT_CLAIM_DIRECTION


@dataclass(frozen=True)
class SelectionRuleSpec:
    """Frozen local compatibility shape for one selected-claim rule."""

    key: SelectionRule
    label: str
    alpha: float
    claim_direction: ClaimDirection
    threshold_working: float | None
    threshold_delta: float | None
    intervals: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class DesignMetric:
    """Frozen local compatibility shape with ``power`` as a real field."""

    true_effect_working: float
    delta: float
    power: float
    type_s: float | None
    type_m: float | None
    expected_selected_abs_z: float | None
    observed_exaggeration: float | None


@dataclass(frozen=True)
class PrecisionTargetResult:
    """Frozen local compatibility shape for one inverse-precision target."""

    target: str
    requested_value: float
    required_se: float | None
    required_information_multiplier: float | None
    approx_95_ci_width_working: float | None
    achieved_power: float | None
    achieved_type_s: float | None
    achieved_type_m: float | None
    note: str


def selection_rule_spec(
    *,
    selection_rule: str = DEFAULT_SELECTION_RULE,
    alpha: float = 0.05,
    null_working: float = 0.0,
    se: float = 1.0,
    claim_direction: str = DEFAULT_CLAIM_DIRECTION,
    threshold_working: float | None = None,
) -> SelectionRuleSpec:
    """Adapt the released core rule result to the frozen local dataclass."""

    result = _core_selection_rule_spec(
        selection_rule=selection_rule,
        alpha=alpha,
        null_working=null_working,
        se=se,
        claim_direction=claim_direction,
        threshold_working=threshold_working,
    )
    return SelectionRuleSpec(
        key=result.key,
        label=result.label,
        alpha=result.alpha,
        claim_direction=result.claim_direction,
        threshold_working=result.threshold_working,
        threshold_delta=result.threshold_delta,
        intervals=result.intervals,
    )


def design_metrics_for_true_effects(
    true_effects_working: Sequence[float] | np.ndarray,
    *,
    null_working: float,
    se: float,
    estimate_working: float | None = None,
    alpha: float = 0.05,
    selection_rule: str = DEFAULT_SELECTION_RULE,
    claim_direction: str = DEFAULT_CLAIM_DIRECTION,
    threshold_working: float | None = None,
    near_null_delta: float = DEFAULT_NEAR_NULL_DELTA,
) -> list[DesignMetric]:
    """Adapt canonical selected-claim metrics to the frozen ``power`` field."""

    results = _core_design_metrics_for_true_effects(
        true_effects_working,
        null_working=null_working,
        se=se,
        estimate_working=estimate_working,
        alpha=alpha,
        selection_rule=selection_rule,
        claim_direction=claim_direction,
        threshold_working=threshold_working,
        near_null_delta=near_null_delta,
    )
    return [
        DesignMetric(
            true_effect_working=result.true_effect_working,
            delta=result.delta,
            power=result.selected_claim_probability,
            type_s=result.type_s,
            type_m=result.type_m,
            expected_selected_abs_z=result.expected_selected_abs_z,
            observed_exaggeration=result.observed_exaggeration,
        )
        for result in results
    ]


def solve_required_delta_for_power(alpha: float, target_power: float) -> float:
    """Delegate the frozen two-sided selected-probability inverse target."""

    return _core_solve_required_delta_for_power(alpha, target_power)


def solve_required_delta_for_type_s(alpha: float, max_type_s: float) -> float:
    """Delegate the frozen two-sided Type S inverse target."""

    return _core_solve_required_delta_for_type_s(alpha, max_type_s)


def solve_required_delta_for_type_m(alpha: float, max_type_m: float) -> float:
    """Delegate the frozen two-sided Type M inverse target."""

    return _core_solve_required_delta_for_type_m(alpha, max_type_m)


def solve_required_precision(
    true_effect_working: float,
    *,
    null_working: float,
    current_se: float,
    alpha: float = 0.05,
    target_power: float | None = None,
    max_type_s: float | None = None,
    max_type_m: float | None = None,
    selection_rule: str = DEFAULT_SELECTION_RULE,
    claim_direction: str = DEFAULT_CLAIM_DIRECTION,
    threshold_working: float | None = None,
    near_null_delta: float = DEFAULT_NEAR_NULL_DELTA,
    z975: float = 1.959963984540054,
) -> dict[str, float | None]:
    """Delegate the aggregate precision solver without changing its mapping."""

    return _core_solve_required_precision(
        true_effect_working,
        null_working=null_working,
        current_se=current_se,
        alpha=alpha,
        target_power=target_power,
        max_type_s=max_type_s,
        max_type_m=max_type_m,
        selection_rule=selection_rule,
        claim_direction=claim_direction,
        threshold_working=threshold_working,
        near_null_delta=near_null_delta,
        z975=z975,
    )


def precision_target_results(
    true_effect_working: float,
    *,
    null_working: float,
    current_se: float,
    alpha: float = 0.05,
    target_power: float | None = None,
    max_type_s: float | None = None,
    max_type_m: float | None = None,
    selection_rule: str = DEFAULT_SELECTION_RULE,
    claim_direction: str = DEFAULT_CLAIM_DIRECTION,
    threshold_working: float | None = None,
    near_null_delta: float = DEFAULT_NEAR_NULL_DELTA,
    z975: float = 1.959963984540054,
) -> list[PrecisionTargetResult]:
    """Adapt released-core precision rows to the frozen local dataclass."""

    results = _core_precision_target_results(
        true_effect_working,
        null_working=null_working,
        current_se=current_se,
        alpha=alpha,
        target_power=target_power,
        max_type_s=max_type_s,
        max_type_m=max_type_m,
        selection_rule=selection_rule,
        claim_direction=claim_direction,
        threshold_working=threshold_working,
        near_null_delta=near_null_delta,
        z975=z975,
    )
    return [
        PrecisionTargetResult(
            target=result.target,
            requested_value=result.requested_value,
            required_se=result.required_se,
            required_information_multiplier=result.required_information_multiplier,
            approx_95_ci_width_working=result.approx_95_ci_width_working,
            achieved_power=result.achieved_power,
            achieved_type_s=result.achieved_type_s,
            achieved_type_m=result.achieved_type_m,
            note=result.note,
        )
        for result in results
    ]
