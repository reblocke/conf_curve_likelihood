"""Wald confidence-curve application package."""

from .core import (
    Z975,
    build_grid,
    confidence_curve,
    estimate_se,
    from_working_scale,
    log_relative_likelihood,
    relative_likelihood,
    summaries,
    to_working_scale,
    validate_inputs,
)
from .design import (
    DesignMetric,
    PrecisionTargetResult,
    SelectionRuleSpec,
    design_metrics_for_true_effects,
    precision_target_results,
    selection_rule_spec,
    solve_required_delta_for_power,
    solve_required_delta_for_type_m,
    solve_required_delta_for_type_s,
    solve_required_precision,
)
from .stage import stage_web_python_package
from .web_contract import compute_curves

__all__ = [
    "DesignMetric",
    "PrecisionTargetResult",
    "SelectionRuleSpec",
    "Z975",
    "build_grid",
    "compute_curves",
    "confidence_curve",
    "design_metrics_for_true_effects",
    "estimate_se",
    "from_working_scale",
    "log_relative_likelihood",
    "precision_target_results",
    "relative_likelihood",
    "selection_rule_spec",
    "solve_required_delta_for_power",
    "solve_required_delta_for_type_m",
    "solve_required_delta_for_type_s",
    "solve_required_precision",
    "stage_web_python_package",
    "summaries",
    "to_working_scale",
    "validate_inputs",
]
