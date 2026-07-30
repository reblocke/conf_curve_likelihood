from __future__ import annotations

import ast
import inspect
from collections import Counter
from dataclasses import fields
from pathlib import Path

import pytest
import wald_inference
import wald_inference.legacy
from wald_inference import EFFECT_SPECS as CORE_EFFECT_SPECS

import confcurve
import confcurve.core as adapter_core
import confcurve.design as adapter_design
import confcurve.models as adapter_models
import confcurve.web_contract as adapter_web_contract

EXPECTED_ALL = [
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

EXPECTED_SIGNATURES = {
    "DesignMetric": (
        "(true_effect_working: 'float', delta: 'float', power: 'float', "
        "type_s: 'float | None', type_m: 'float | None', "
        "expected_selected_abs_z: 'float | None', "
        "observed_exaggeration: 'float | None') -> None"
    ),
    "PrecisionTargetResult": (
        "(target: 'str', requested_value: 'float', required_se: 'float | None', "
        "required_information_multiplier: 'float | None', "
        "approx_95_ci_width_working: 'float | None', achieved_power: 'float | None', "
        "achieved_type_s: 'float | None', achieved_type_m: 'float | None', "
        "note: 'str') -> None"
    ),
    "SelectionRuleSpec": (
        "(key: 'SelectionRule', label: 'str', alpha: 'float', "
        "claim_direction: 'ClaimDirection', threshold_working: 'float | None', "
        "threshold_delta: 'float | None', "
        "intervals: 'tuple[tuple[float, float], ...]') -> None"
    ),
    "build_grid": (
        "(theta_hat: 'float', se: 'float', span_multiplier: 'float' = 4.5, "
        "n: 'int' = 801, include_values: 'Sequence[float] | None' = None, "
        "max_span: 'float | None' = None) -> 'np.ndarray'"
    ),
    "compute_curves": "(payload: 'CurveRequest | dict[str, Any]') -> 'CurveResponse'",
    "confidence_curve": (
        "(theta: 'float | np.ndarray', theta_hat: 'float', se: 'float') -> 'np.ndarray'"
    ),
    "design_metrics_for_true_effects": (
        "(true_effects_working: 'Sequence[float] | np.ndarray', *, "
        "null_working: 'float', se: 'float', estimate_working: 'float | None' = None, "
        "alpha: 'float' = 0.05, selection_rule: 'str' = 'two_sided_p_lt_alpha', "
        "claim_direction: 'str' = 'positive', threshold_working: 'float | None' = None, "
        "near_null_delta: 'float' = 1e-12) -> 'list[DesignMetric]'"
    ),
    "estimate_se": "(theta_hat: 'float', lower: 'float', upper: 'float') -> 'float'",
    "from_working_scale": (
        "(effect_type: 'str', values: 'float | Sequence[float] | np.ndarray') "
        "-> 'float | np.ndarray'"
    ),
    "log_relative_likelihood": (
        "(theta: 'float | np.ndarray', theta_hat: 'float', se: 'float') -> 'np.ndarray'"
    ),
    "precision_target_results": (
        "(true_effect_working: 'float', *, null_working: 'float', current_se: 'float', "
        "alpha: 'float' = 0.05, target_power: 'float | None' = None, "
        "max_type_s: 'float | None' = None, max_type_m: 'float | None' = None, "
        "selection_rule: 'str' = 'two_sided_p_lt_alpha', "
        "claim_direction: 'str' = 'positive', threshold_working: 'float | None' = None, "
        "near_null_delta: 'float' = 1e-12, z975: 'float' = 1.959963984540054) "
        "-> 'list[PrecisionTargetResult]'"
    ),
    "relative_likelihood": (
        "(theta: 'float | np.ndarray', theta_hat: 'float', se: 'float') -> 'np.ndarray'"
    ),
    "selection_rule_spec": (
        "(*, selection_rule: 'str' = 'two_sided_p_lt_alpha', alpha: 'float' = 0.05, "
        "null_working: 'float' = 0.0, se: 'float' = 1.0, "
        "claim_direction: 'str' = 'positive', "
        "threshold_working: 'float | None' = None) -> 'SelectionRuleSpec'"
    ),
    "solve_required_delta_for_power": ("(alpha: 'float', target_power: 'float') -> 'float'"),
    "solve_required_delta_for_type_m": ("(alpha: 'float', max_type_m: 'float') -> 'float'"),
    "solve_required_delta_for_type_s": ("(alpha: 'float', max_type_s: 'float') -> 'float'"),
    "solve_required_precision": (
        "(true_effect_working: 'float', *, null_working: 'float', current_se: 'float', "
        "alpha: 'float' = 0.05, target_power: 'float | None' = None, "
        "max_type_s: 'float | None' = None, max_type_m: 'float | None' = None, "
        "selection_rule: 'str' = 'two_sided_p_lt_alpha', "
        "claim_direction: 'str' = 'positive', threshold_working: 'float | None' = None, "
        "near_null_delta: 'float' = 1e-12, z975: 'float' = 1.959963984540054) "
        "-> 'dict[str, float | None]'"
    ),
    "stage_web_python_package": "(target_dir: 'Path') -> 'list[Path]'",
    "summaries": (
        "(theta_hat: 'float', se: 'float', null_value: 'float') -> 'dict[str, float | None]'"
    ),
    "to_working_scale": (
        "(effect_type: 'str', values: 'float | Sequence[float] | np.ndarray') "
        "-> 'float | np.ndarray'"
    ),
    "validate_inputs": (
        "(effect_type: 'str' = 'odds_ratio', estimate: 'float | int | None' = None, "
        "lower: 'float | int | None' = None, upper: 'float | int | None' = None, "
        "null_value: 'float | int | None' = None, "
        "thresholds: 'Sequence[float] | None' = None, "
        "display_range_lower: 'float | int | None' = None, "
        "display_range_upper: 'float | int | None' = None, "
        "display_natural_axis: 'bool' = True, grid_points: 'int' = 801, "
        "show_cutoffs: 'bool' = True) -> 'ValidatedInputs'"
    ),
}

EXPECTED_DATACLASS_FIELDS = {
    adapter_models.EffectSpec: [
        "key",
        "label",
        "family",
        "working_scale",
        "default_null",
        "positive_only",
    ],
    adapter_core.ValidatedInputs: [
        "effect_spec",
        "estimate",
        "estimate_source",
        "provided_estimate",
        "lower",
        "upper",
        "null_value",
        "thresholds",
        "display_range_working",
        "display_natural_axis",
        "grid_points",
        "show_cutoffs",
        "default_null_applied",
        "warnings",
    ],
    adapter_core.StandardErrorEstimate: [
        "se",
        "method",
        "se_lower",
        "se_upper",
        "se_width",
        "relative_asymmetry",
    ],
    adapter_design.SelectionRuleSpec: [
        "key",
        "label",
        "alpha",
        "claim_direction",
        "threshold_working",
        "threshold_delta",
        "intervals",
    ],
    adapter_design.DesignMetric: [
        "true_effect_working",
        "delta",
        "power",
        "type_s",
        "type_m",
        "expected_selected_abs_z",
        "observed_exaggeration",
    ],
    adapter_design.PrecisionTargetResult: [
        "target",
        "requested_value",
        "required_se",
        "required_information_multiplier",
        "approx_95_ci_width_working",
        "achieved_power",
        "achieved_type_s",
        "achieved_type_m",
        "note",
    ],
}


def test_public_exports_and_signatures_match_the_frozen_contract() -> None:
    assert confcurve.__version__ == "0.2.4"
    assert confcurve.__all__ == EXPECTED_ALL
    assert set(EXPECTED_SIGNATURES) == {
        name for name in confcurve.__all__ if callable(getattr(confcurve, name))
    }
    assert {
        name: str(inspect.signature(getattr(confcurve, name))) for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES


def test_local_dataclass_shapes_remain_frozen() -> None:
    for data_class, expected_fields in EXPECTED_DATACLASS_FIELDS.items():
        assert [field.name for field in fields(data_class)] == expected_fields
        assert data_class.__dataclass_params__.frozen is True

    power_field = adapter_design.DesignMetric.__dataclass_fields__["power"]
    assert power_field.name == "power"
    assert not isinstance(
        inspect.getattr_static(adapter_design.DesignMetric, "power", None),
        property,
    )


def test_validation_error_and_effect_metadata_are_exact_core_adapters() -> None:
    assert adapter_core.ValidationError is wald_inference.ValidationError
    assert list(adapter_models.EFFECT_SPECS) == list(CORE_EFFECT_SPECS)
    assert {
        key: tuple(getattr(spec, field.name) for field in fields(spec))
        for key, spec in adapter_models.EFFECT_SPECS.items()
    } == {
        key: tuple(getattr(spec, field.name) for field in fields(adapter_models.EffectSpec))
        for key, spec in CORE_EFFECT_SPECS.items()
    }


@pytest.mark.parametrize(
    ("kwargs", "expected_message"),
    [
        pytest.param(
            {
                "effect_type": "not_an_effect",
                "lower": None,
                "upper": None,
                "thresholds": "invalid",
            },
            (
                "Unsupported effect type 'not_an_effect'. Expected one of: hazard_ratio, "
                "incidence_rate_ratio, mean_difference, odds_ratio, rate_difference, "
                "ratio_of_means, regression_coefficient, risk_difference, risk_ratio."
            ),
            id="effect-type-before-required-ci",
        ),
        pytest.param(
            {
                "lower": None,
                "upper": None,
                "thresholds": "invalid",
                "display_range_lower": 0.5,
            },
            "Lower and upper confidence limits are required.",
            id="required-ci-before-thresholds-and-display",
        ),
        pytest.param(
            {
                "lower": float("nan"),
                "upper": float("nan"),
                "estimate": float("nan"),
                "null_value": float("nan"),
                "thresholds": "invalid",
            },
            "Lower confidence limit must be finite.",
            id="lower-finite-before-other-finiteness",
        ),
        pytest.param(
            {
                "lower": 2.0,
                "upper": float("inf"),
                "estimate": float("nan"),
                "null_value": float("nan"),
                "thresholds": "invalid",
            },
            "Upper confidence limit must be finite.",
            id="upper-finite-before-estimate",
        ),
        pytest.param(
            {
                "lower": 2.0,
                "upper": 1.0,
                "estimate": float("nan"),
                "null_value": float("nan"),
                "thresholds": "invalid",
            },
            "Estimate must be finite.",
            id="estimate-finite-before-ci-ordering",
        ),
        pytest.param(
            {
                "lower": 2.0,
                "upper": 1.0,
                "null_value": float("nan"),
                "thresholds": "invalid",
            },
            "The lower confidence limit must be less than the upper confidence limit.",
            id="ci-ordering-before-null-and-thresholds",
        ),
        pytest.param(
            {
                "lower": 1.0,
                "upper": 2.0,
                "null_value": float("nan"),
                "thresholds": "invalid",
                "display_range_lower": 0.5,
            },
            "Null value must be finite.",
            id="null-finite-before-thresholds-and-display",
        ),
        pytest.param(
            {
                "lower": 1.0,
                "upper": 2.0,
                "thresholds": "invalid",
                "display_range_lower": 0.5,
            },
            "Thresholds must be supplied as numeric values, not a string.",
            id="threshold-shape-before-display-pair",
        ),
        pytest.param(
            {
                "lower": 1.0,
                "upper": 2.0,
                "thresholds": [float("nan")],
                "display_range_lower": 0.5,
            },
            "Threshold values must be finite.",
            id="threshold-finite-before-display-pair",
        ),
        pytest.param(
            {
                "lower": -2.0,
                "upper": -1.0,
                "thresholds": [0.0],
                "display_range_lower": 0.5,
            },
            "Plausible display range lower and upper must be supplied together.",
            id="display-pair-before-combined-ratio-positivity",
        ),
        pytest.param(
            {
                "lower": -2.0,
                "upper": -1.0,
                "thresholds": [0.0],
                "display_range_lower": float("nan"),
                "display_range_upper": 2.0,
            },
            "Plausible display range lower must be finite.",
            id="display-finite-before-combined-ratio-positivity",
        ),
        pytest.param(
            {
                "lower": -2.0,
                "upper": -1.0,
                "estimate": 10.0,
                "null_value": 1.0,
                "thresholds": [0.0],
            },
            "Odds ratio inputs must be strictly positive on the natural scale.",
            id="combined-ratio-positivity-before-reconstruction-consistency",
        ),
        pytest.param(
            {
                "lower": 1.0,
                "upper": 2.0,
                "estimate": 10.0,
                "grid_points": 1,
            },
            (
                "Provided estimate is inconsistent with the supplied 95% confidence interval "
                "on the working scale beyond the rounding tolerance."
            ),
            id="reconstruction-consistency-before-grid-size",
        ),
    ],
)
def test_validate_inputs_preserves_frozen_compound_invalid_exception_precedence(
    kwargs: dict[str, object],
    expected_message: str,
) -> None:
    """These exact messages/order were captured from pre-split commit 830756ec."""

    with pytest.raises(adapter_core.ValidationError) as caught:
        adapter_core.validate_inputs(**kwargs)

    assert str(caught.value) == expected_message


def _module_tree(module: object) -> ast.Module:
    source_path = Path(inspect.getsourcefile(module) or "")
    return ast.parse(source_path.read_text(encoding="utf-8"))


def _function_node(module: object, function_name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in _module_tree(module).body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    ]
    [function] = matches
    return function


def _call_counter(module: object, function_name: str) -> Counter[str]:
    function = _function_node(module, function_name)
    return Counter(
        ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)
    )


def test_direct_formula_wrappers_are_exact_single_call_delegations() -> None:
    expected_wrappers = {
        adapter_core: {
            "to_working_scale": "_legacy.to_working_scale",
            "from_working_scale": "_legacy.from_working_scale",
            "critical_effect_distance": "_core_critical_effect_distance",
            "critical_effect_markers": "_core_critical_effect_markers",
            "estimate_se": "_legacy.estimate_se",
            "build_grid": "_legacy.build_grid",
            "standardized_distance": "_core_standardized_distance",
            "confidence_curve": "_legacy.confidence_curve",
            "relative_likelihood": "_legacy.relative_likelihood",
            "log_relative_likelihood": "_legacy.log_relative_likelihood",
            "max_safe_grid_span": "_core_max_safe_grid_span",
            "summaries": "_legacy.summaries",
            "asymmetry_warning": "_core_asymmetry_warning",
        },
        adapter_design: {
            "solve_required_delta_for_power": "_core_solve_required_delta_for_power",
            "solve_required_delta_for_type_s": "_core_solve_required_delta_for_type_s",
            "solve_required_delta_for_type_m": "_core_solve_required_delta_for_type_m",
            "solve_required_precision": "_core_solve_required_precision",
        },
    }

    for module, wrappers in expected_wrappers.items():
        for function_name, target in wrappers.items():
            function = _function_node(module, function_name)
            body = function.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body = body[1:]
            assert len(body) == 1, function_name
            [statement] = body
            assert isinstance(statement, ast.Return), function_name
            assert isinstance(statement.value, ast.Call), function_name
            assert ast.unparse(statement.value.func) == target, function_name


def test_formula_wrapper_aliases_resolve_to_the_exact_upstream_functions() -> None:
    expected_aliases = {
        adapter_core: {
            "_core_estimate_se_details": wald_inference.estimate_se_details,
            "_core_critical_effect_distance": wald_inference.legacy_critical_effect_distance,
            "_core_critical_effect_markers": wald_inference.legacy_critical_effect_markers,
            "_core_max_safe_grid_span": wald_inference.max_safe_grid_span,
            "_core_standardized_distance": wald_inference.standardized_distance,
            "_core_asymmetry_warning": wald_inference.legacy.asymmetry_warning,
        },
        adapter_design: {
            "_core_design_metrics_for_true_effects": (
                wald_inference.design_metrics_for_true_effects
            ),
            "_core_precision_target_results": wald_inference.precision_target_results,
            "_core_selection_rule_spec": wald_inference.selection_rule_spec,
            "_core_solve_required_delta_for_power": (wald_inference.solve_required_delta_for_power),
            "_core_solve_required_delta_for_type_s": (
                wald_inference.solve_required_delta_for_type_s
            ),
            "_core_solve_required_delta_for_type_m": (
                wald_inference.solve_required_delta_for_type_m
            ),
            "_core_solve_required_precision": wald_inference.solve_required_precision,
        },
    }
    for module, aliases in expected_aliases.items():
        for alias, expected in aliases.items():
            assert getattr(module, alias) is expected, alias

    assert adapter_core._legacy is wald_inference.legacy


def test_compatibility_constants_only_use_documented_core_surfaces() -> None:
    core_legacy_constants = (
        "ASYMMETRY_RELATIVE_TOLERANCE",
        "DEFAULT_GRID_POINTS",
        "DEFAULT_SPAN_MULTIPLIER",
        "ESTIMATE_MATCH_ABSOLUTE_TOLERANCE",
        "ESTIMATE_MATCH_RELATIVE_TOLERANCE",
        "GRID_EXPANSION_PADDING_MULTIPLIER",
        "LOG_MAX_FLOAT",
        "MAX_FINITE_ABS_Z",
        "MAX_FINITE_SPAN",
        "MAX_FLOAT",
        "Z80",
        "Z975",
    )
    for name in core_legacy_constants:
        assert getattr(adapter_core, name) == getattr(wald_inference.legacy, name)
    for name in ("DEFAULT_SOLVER_TOLERANCE", "MAX_INFORMATION_MULTIPLIER"):
        assert getattr(adapter_design, name) == getattr(wald_inference.legacy, name)

    for module in (adapter_core, adapter_design):
        internal_imports = {
            node.module
            for node in ast.walk(_module_tree(module))
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("wald_inference.")
            and node.module != "wald_inference.legacy"
        }
        assert internal_imports == set()


def test_dataclass_adapters_only_call_the_upstream_and_local_shape_constructor() -> None:
    assert _call_counter(adapter_core, "estimate_se_details") == Counter(
        {"_core_estimate_se_details": 1, "StandardErrorEstimate": 1}
    )
    assert _call_counter(adapter_design, "selection_rule_spec") == Counter(
        {"_core_selection_rule_spec": 1, "SelectionRuleSpec": 1}
    )
    assert _call_counter(adapter_design, "design_metrics_for_true_effects") == Counter(
        {"_core_design_metrics_for_true_effects": 1, "DesignMetric": 1}
    )
    assert _call_counter(adapter_design, "precision_target_results") == Counter(
        {"_core_precision_target_results": 1, "PrecisionTargetResult": 1}
    )
    assert _call_counter(adapter_core, "validate_inputs")["reconstruct_wald_from_95_ci"] == 1


def test_formula_adapters_do_not_import_scipy_or_reimplement_numpy_math() -> None:
    forbidden_numpy_calls = {"exp", "expm1", "log", "log1p", "sqrt", "square"}

    for module in (adapter_core, adapter_design, adapter_web_contract):
        tree = _module_tree(module)
        scipy_imports = [
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.Import)
                and any(
                    alias.name == "scipy" or alias.name.startswith("scipy.") for alias in node.names
                )
            )
            or (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and (node.module == "scipy" or node.module.startswith("scipy."))
            )
        ]
        numpy_formula_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "np"
            and node.func.attr in forbidden_numpy_calls
        ]

        assert scipy_imports == []
        assert numpy_formula_calls == []


def test_web_contract_delegates_numerical_work_and_only_owns_display_arithmetic() -> None:
    expected_calls = {
        "_safe_display_values": Counter({"from_working_scale": 2}),
        "_threshold_support_summaries": Counter({"support_comparison": 1}),
        "_s_minus_2_interval": Counter({"support_interval": 1}),
        "_precision_target_payloads": Counter({"precision_target_results": 1}),
        "_design_payload": Counter(
            {
                "information_scaled_standard_error": 1,
                "approximate_wald_ci_width": 2,
                "selection_rule_spec": 1,
                "design_metrics_for_true_effects": 2,
            }
        ),
        "compute_curves": Counter(
            {
                "validate_inputs": 1,
                "estimate_se_details": 2,
                "critical_effect_distance": 1,
                "critical_effect_markers": 1,
                "max_safe_grid_span": 1,
                "build_grid": 1,
                "standardized_distance": 1,
                "confidence_curve": 1,
                "relative_likelihood": 1,
                "log_relative_likelihood": 1,
                "asymmetry_warning": 1,
                "summaries": 1,
            }
        ),
    }
    for function_name, required_calls in expected_calls.items():
        observed = _call_counter(adapter_web_contract, function_name)
        for call, count in required_calls.items():
            assert observed[call] == count, (function_name, call)

    arithmetic_operators = (
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.MatMult,
    )
    observed_arithmetic: dict[str, Counter[str]] = {}
    for function in (
        node
        for node in _module_tree(adapter_web_contract).body
        if isinstance(node, ast.FunctionDef)
    ):
        expressions = Counter(
            ast.unparse(node)
            for node in ast.walk(function)
            if isinstance(node, ast.BinOp) and isinstance(node.op, arithmetic_operators)
        )
        if expressions:
            observed_arithmetic[function.name] = expressions

    assert observed_arithmetic == {
        "_deduplicate_scenarios": Counter(
            {
                "abs(value) * 1e-10": 1,
                "value - previous": 1,
                "abs(previous) * 1e-10": 1,
            }
        ),
        "compute_curves": Counter({"value - theta_hat": 1}),
    }
