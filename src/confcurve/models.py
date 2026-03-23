from __future__ import annotations

from typing import TypedDict


class CurveRequest(TypedDict, total=False):
    effect_type: str
    estimate: float
    lower: float
    upper: float
    null_value: float
    thresholds: list[float]
    display_natural_axis: bool
    grid_points: int
    show_cutoffs: bool


class CurveResponse(TypedDict):
    meta: dict[str, object]
    summary: dict[str, object]
    warnings: list[str]
    grid: dict[str, list[float]]
