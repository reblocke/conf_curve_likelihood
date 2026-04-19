from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

EffectFamily = Literal["additive", "ratio"]
WorkingScale = Literal["identity", "log"]
EstimateSource = Literal["inferred_from_ci", "provided_validated"]


@dataclass(frozen=True)
class EffectSpec:
    key: str
    label: str
    family: EffectFamily
    working_scale: WorkingScale
    default_null: float
    positive_only: bool


EFFECT_SPECS: dict[str, EffectSpec] = {
    "odds_ratio": EffectSpec(
        key="odds_ratio",
        label="Odds ratio",
        family="ratio",
        working_scale="log",
        default_null=1.0,
        positive_only=True,
    ),
    "risk_ratio": EffectSpec(
        key="risk_ratio",
        label="Risk ratio",
        family="ratio",
        working_scale="log",
        default_null=1.0,
        positive_only=True,
    ),
    "hazard_ratio": EffectSpec(
        key="hazard_ratio",
        label="Hazard ratio",
        family="ratio",
        working_scale="log",
        default_null=1.0,
        positive_only=True,
    ),
    "incidence_rate_ratio": EffectSpec(
        key="incidence_rate_ratio",
        label="Incidence rate ratio",
        family="ratio",
        working_scale="log",
        default_null=1.0,
        positive_only=True,
    ),
    "ratio_of_means": EffectSpec(
        key="ratio_of_means",
        label="Ratio of means",
        family="ratio",
        working_scale="log",
        default_null=1.0,
        positive_only=True,
    ),
    "mean_difference": EffectSpec(
        key="mean_difference",
        label="Mean difference",
        family="additive",
        working_scale="identity",
        default_null=0.0,
        positive_only=False,
    ),
    "risk_difference": EffectSpec(
        key="risk_difference",
        label="Risk difference",
        family="additive",
        working_scale="identity",
        default_null=0.0,
        positive_only=False,
    ),
    "rate_difference": EffectSpec(
        key="rate_difference",
        label="Rate difference",
        family="additive",
        working_scale="identity",
        default_null=0.0,
        positive_only=False,
    ),
    "regression_coefficient": EffectSpec(
        key="regression_coefficient",
        label="Regression coefficient",
        family="additive",
        working_scale="identity",
        default_null=0.0,
        positive_only=False,
    ),
}

DEFAULT_EFFECT_TYPE = "odds_ratio"


class CurveRequest(TypedDict, total=False):
    effect_type: str
    estimate: float | None
    lower: float
    upper: float
    null_value: float
    thresholds: list[float]
    display_range_lower: float | None
    display_range_upper: float | None
    display_natural_axis: bool
    grid_points: int
    show_cutoffs: bool


class ThresholdSupportPayload(TypedDict):
    threshold_display: float
    threshold_working: float
    relative_likelihood: float
    log_relative_likelihood: float
    likelihood_ratio_mle_to_threshold: float | None
    log_likelihood_ratio_mle_to_threshold: float
    likelihood_ratio_threshold_to_null: float | None
    log_likelihood_ratio_threshold_to_null: float | None
    direction_from_estimate: str
    direction_from_null: str


class MetaPayload(TypedDict):
    effect_spec: dict[str, object]
    display_axis_scale: str
    estimate_source: EstimateSource
    default_null_applied: bool
    grid_points: int
    show_cutoffs: bool
    se_method: str
    relative_asymmetry: float
    thresholds_display: list[float]
    thresholds_working: list[float]
    display_range_active: bool
    display_range_display: list[float] | None
    display_range_working: list[float] | None
    threshold_support_summaries: list[ThresholdSupportPayload]


class SummaryPayload(TypedDict):
    estimate_display: float
    estimate_working: float
    ci_display: list[float]
    ci_working: list[float]
    null_display: float
    null_working: float
    working_scale_se: float
    null_relative_likelihood: float
    log_null_relative_likelihood: float | None
    likelihood_ratio_mle_to_null: float | None
    log_likelihood_ratio_mle_to_null: float | None
    two_sided_wald_p_value: float
    null_z_value: float | None
    critical_effect_markers_display: list[float]
    critical_effect_markers_working: list[float]
    critical_effect_distance_working: float


class GridPayload(TypedDict):
    effect_display: list[float]
    effect_working: list[float]
    z: list[float]
    compatibility: list[float]
    relative_likelihood: list[float]
    log_relative_likelihood: list[float]


class CurveResponse(TypedDict):
    meta: MetaPayload
    summary: SummaryPayload
    warnings: list[str]
    grid: GridPayload
