from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from confcurve.core import ValidationError
from confcurve.models import EFFECT_SPECS
from confcurve.web_contract import compute_curves

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = PROJECT_ROOT / "tests" / "golden"
REQUESTS_ROOT = GOLDEN_ROOT / "requests"
RESPONSES_ROOT = GOLDEN_ROOT / "responses"
SCHEMAS_ROOT = GOLDEN_ROOT / "export_schemas"
MANIFEST_PATH = GOLDEN_ROOT / "manifest.json"

SOURCE_REPOSITORY = "reblocke/conf_curve_likelihood"
SOURCE_BRANCH = "main"
SOURCE_COMMIT = "830756ecb11b4e8161f8dfe1fc75afc346ef4467"
BASELINE_DATE = "2026-07-29"
FIXTURE_SCHEMA_VERSION = 1
RTOL = 1e-12
ATOL = 1e-14
EXACT_FLOAT_PATHS = ("$.response.meta.effect_spec.default_null",)
DEPENDENCY_AUTHORITY_FILES = ("pyproject.toml", "uv.lock", ".python-version")

FixtureKind = Literal["full_contract", "edge_summary", "expected_error"]


@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    matrix_case: str
    description: str
    request: dict[str, Any]
    fixture_kind: FixtureKind


def _cases() -> tuple[GoldenCase, ...]:
    max_float = sys.float_info.max
    ordinary = (
        GoldenCase(
            "B01",
            "B01",
            "Additive observed reconstruction",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "null_value": 0.0,
                "thresholds": [0.2],
                "grid_points": 401,
            },
            "full_contract",
        ),
        GoldenCase(
            "B02",
            "B02",
            "Ratio observed reconstruction on the natural display scale",
            {
                "effect_type": "odds_ratio",
                "lower": 1.2,
                "upper": 2.7,
                "null_value": 1.0,
                "thresholds": [1.25],
                "display_natural_axis": True,
                "grid_points": 401,
            },
            "full_contract",
        ),
        GoldenCase(
            "B03",
            "B03",
            "Presentation-only ratio display window",
            {
                "effect_type": "odds_ratio",
                "lower": 1.2,
                "upper": 2.7,
                "null_value": 1.0,
                "thresholds": [1.25],
                "display_range_lower": 0.9,
                "display_range_upper": 1.1,
                "grid_points": 401,
            },
            "full_contract",
        ),
        GoldenCase(
            "B04",
            "B04",
            "Forward two-sided design calibration",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "thresholds": [0.2],
                "design_enabled": True,
                "design_alpha": 0.05,
                "design_selection_rule": "two_sided_p_lt_alpha",
                "design_true_effects": [0.1, 0.3],
                "grid_points": 401,
            },
            "full_contract",
        ),
        GoldenCase(
            "B05",
            "B05",
            "Directional threshold rule on a ratio scale",
            {
                "effect_type": "odds_ratio",
                "lower": 1.2,
                "upper": 2.7,
                "design_enabled": True,
                "design_alpha": 0.05,
                "design_selection_rule": "ci_excludes_mcid",
                "design_claim_direction": "positive",
                "design_claim_threshold": 1.25,
                "design_information_multiplier": 4.0,
                "design_true_effects": [1.1, 1.5, 2.0],
                "grid_points": 401,
            },
            "full_contract",
        ),
        GoldenCase(
            "B06",
            "B06",
            "Inverse precision targets",
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
            },
            "full_contract",
        ),
    )
    undefined_and_invalid = (
        GoldenCase(
            "B07a-null",
            "B07",
            "Precision target exactly at the null is undefined",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_precision_target_effect": 0.0,
                "design_target_power": 0.8,
                "grid_points": 401,
            },
            "edge_summary",
        ),
        GoldenCase(
            "B07b-near-null",
            "B07",
            "Near-null precision target and assumed true-effect scenario are undefined",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_information_multiplier": 0.01,
                "design_precision_target_effect": 1e-14,
                "design_target_power": 0.8,
                "design_true_effects": [1.2e-12],
                "grid_points": 401,
            },
            "edge_summary",
        ),
        GoldenCase(
            "B07c-threshold-infeasible",
            "B07",
            "Positive threshold-conditioned target below the threshold is infeasible",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_selection_rule": "ci_excludes_mcid",
                "design_claim_direction": "positive",
                "design_claim_threshold": 0.2,
                "design_precision_target_effect": 0.1,
                "design_target_power": 0.8,
                "grid_points": 401,
            },
            "edge_summary",
        ),
        GoldenCase(
            "B07d-alpha-zero",
            "B07",
            "Design alpha of zero is invalid",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_alpha": 0,
            },
            "expected_error",
        ),
        GoldenCase(
            "B07e-alpha-one",
            "B07",
            "Design alpha of one is invalid",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_alpha": 1,
            },
            "expected_error",
        ),
        GoldenCase(
            "B07f-alpha-nonnumeric",
            "B07",
            "Nonnumeric design alpha is invalid",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_alpha": "not-a-number",
            },
            "expected_error",
        ),
        GoldenCase(
            "B07g-alpha-underflow",
            "B07",
            "Underflowing design tail probability is rejected",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_alpha": 1e-320,
            },
            "expected_error",
        ),
        GoldenCase(
            "B07h-display-range-pair",
            "B07",
            "A display range requires both bounds",
            {
                "effect_type": "odds_ratio",
                "lower": 1.2,
                "upper": 2.7,
                "display_range_lower": 0.9,
            },
            "expected_error",
        ),
        GoldenCase(
            "B07i-design-range-pair",
            "B07",
            "A design plausible range requires both bounds",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "design_enabled": True,
                "design_plausible_range_lower": -0.2,
            },
            "expected_error",
        ),
        GoldenCase(
            "B07j-ratio-positive",
            "B07",
            "Natural-scale ratio inputs must be positive",
            {
                "effect_type": "odds_ratio",
                "lower": 0,
                "upper": 2.7,
            },
            "expected_error",
        ),
        GoldenCase(
            "B07k-disabled-design-ignored",
            "B07",
            "Disabled design fields are ignored and leave the observed contract unchanged",
            {
                "effect_type": "mean_difference",
                "lower": 0.11,
                "upper": 0.73,
                "null_value": 0.0,
                "thresholds": [0.2],
                "grid_points": 401,
                "design_enabled": False,
                "design_alpha": "not-a-number",
                "design_selection_rule": "unsupported-rule",
                "design_claim_direction": "sideways",
                "design_claim_threshold": "not-a-number",
                "design_information_multiplier": -1,
                "design_precision_target_effect": "not-a-number",
                "design_target_power": 2,
                "design_max_type_s": -1,
                "design_max_type_m": 0,
                "design_true_effects": ["not-a-number"],
                "design_plausible_range_lower": 1,
            },
            "full_contract",
        ),
    )
    extremes = (
        GoldenCase(
            "B08a-additive-midpoint",
            "B08",
            "Opposite-signed extreme additive bounds use a safe finite midpoint",
            {
                "effect_type": "mean_difference",
                "lower": -1e308,
                "upper": 1e308,
                "null_value": 0.0,
                "grid_points": 401,
            },
            "edge_summary",
        ),
        GoldenCase(
            "B08b-s-minus-2-clipping",
            "B08",
            "Extreme additive S-2 endpoints are clipped to finite values",
            {
                "effect_type": "mean_difference",
                "lower": 1e308,
                "upper": 1.79e308,
                "grid_points": 401,
            },
            "edge_summary",
        ),
        GoldenCase(
            "B08c-log-likelihood-fallback",
            "B08",
            "Extreme likelihood ratio falls back to a finite log-scale result",
            {
                "effect_type": "mean_difference",
                "lower": -0.0001,
                "upper": 0.0001,
                "null_value": 100.0,
                "grid_points": 401,
            },
            "edge_summary",
        ),
        GoldenCase(
            "B08d-ratio-natural-clipping",
            "B08",
            "Near-maximum ratio bounds remain finite on the natural display axis",
            {
                "effect_type": "odds_ratio",
                "lower": max_float / 2.0,
                "upper": max_float,
                "display_natural_axis": True,
                "grid_points": 401,
            },
            "edge_summary",
        ),
        GoldenCase(
            "B08e-unrepresentable-design-distance",
            "B08",
            "Unrepresentable finite design distance is rejected before JSON serialization",
            {
                "effect_type": "mean_difference",
                "lower": -1e-320,
                "upper": 1e-320,
                "null_value": 1e308,
                "design_enabled": True,
                "grid_points": 401,
            },
            "expected_error",
        ),
    )
    return ordinary + undefined_and_invalid + extremes


def _canonical_json(value: Any) -> str:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _dependency_versions() -> dict[str, str]:
    return {
        "confcurve": importlib.metadata.version("confcurve"),
        "numpy": importlib.metadata.version("numpy"),
        "scipy": importlib.metadata.version("scipy"),
        "pytest": importlib.metadata.version("pytest"),
        "hypothesis": importlib.metadata.version("hypothesis"),
        "playwright": importlib.metadata.version("playwright"),
        "pytest-playwright": importlib.metadata.version("pytest-playwright"),
        "pyodide": "0.29.3",
        "plotly": "3.1.0",
        "python_declared": (PROJECT_ROOT / ".python-version").read_text(encoding="utf-8").strip(),
        "python_runtime": platform.python_version(),
    }


def _python_series(version: str) -> str:
    return ".".join(version.split(".")[:2])


def _dependency_version_mismatches(
    recorded: Any,
    *,
    path: str,
) -> list[str]:
    if not isinstance(recorded, dict):
        return [f"{path}: expected an object"]
    current = _dependency_versions()
    mismatches: list[str] = []
    if set(recorded) != set(current):
        missing = sorted(set(current) - set(recorded))
        unexpected = sorted(set(recorded) - set(current))
        if missing:
            mismatches.append(f"{path}: missing keys {missing!r}")
        if unexpected:
            mismatches.append(f"{path}: unexpected keys {unexpected!r}")
        return mismatches
    declared_series = _python_series(current["python_declared"])
    if _python_series(current["python_runtime"]) != declared_series:
        mismatches.append(
            f"{path}.python_runtime: current runtime {current['python_runtime']!r} "
            f"is outside declared Python {current['python_declared']!r}"
        )
    for key, current_value in current.items():
        recorded_value = recorded[key]
        if key == "python_runtime":
            if (
                not isinstance(recorded_value, str)
                or _python_series(recorded_value) != declared_series
            ):
                mismatches.append(
                    f"{path}.python_runtime: recorded generation runtime "
                    f"{recorded_value!r} is outside declared Python "
                    f"{current['python_declared']!r}"
                )
        elif recorded_value != current_value:
            mismatches.append(
                f"{path}.{key}: expected {current_value!r}, observed {recorded_value!r}"
            )
    return mismatches


def _sequence_summary(values: Sequence[Any]) -> dict[str, Any]:
    finite = True
    for value in values:
        if value is not None and isinstance(value, (int, float)) and not isinstance(value, bool):
            finite = finite and math.isfinite(float(value))
    return {
        "length": len(values),
        "first": values[0] if values else None,
        "last": values[-1] if values else None,
        "none_count": sum(value is None for value in values),
        "all_numeric_values_finite": finite,
    }


def _edge_summary(response: dict[str, Any]) -> dict[str, Any]:
    design = response["design"]
    design_summary = None
    if design is not None:
        design_summary = {
            "config": design["config"],
            "grid": {key: _sequence_summary(values) for key, values in design["grid"].items()},
            "scenarios": design["scenarios"],
            "precision_targets": design["precision_targets"],
            "warnings": design["warnings"],
        }
    return {
        "meta": response["meta"],
        "summary": response["summary"],
        "warnings": response["warnings"],
        "grid": {key: _sequence_summary(values) for key, values in response["grid"].items()},
        "design": design_summary,
    }


def _evaluate_case(case: GoldenCase) -> dict[str, Any]:
    try:
        response = compute_curves(case.request)
    except ValidationError as exc:
        if case.fixture_kind != "expected_error":
            raise
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
    if case.fixture_kind == "expected_error":
        raise AssertionError(f"{case.case_id} expected ValidationError but computation succeeded")
    json.dumps(response, allow_nan=False)
    payload = response if case.fixture_kind == "full_contract" else _edge_summary(response)
    return {"status": "success", "response": payload}


def _field(
    field_type: str,
    *,
    nullable: bool,
    units: str,
    meaning: str,
    conditioning: str,
) -> dict[str, Any]:
    return {
        "type": field_type,
        "nullable": nullable,
        "units_or_scale": units,
        "meaning": meaning,
        "conditioning": conditioning,
    }


def _request_runtime_contract() -> dict[str, dict[str, Any]]:
    """Document runtime presence/default/null behavior beyond total=False typing."""

    def runtime(
        *,
        required: bool,
        has_default: bool,
        default: Any,
        omission: str,
        null_accepted: bool,
        explicit_null: str,
    ) -> dict[str, Any]:
        return {
            "required": required,
            "has_omission_default": has_default,
            "omission_default": default,
            "omission_behavior": omission,
            "explicit_null_accepted": null_accepted,
            "explicit_null_behavior": explicit_null,
        }

    ignored = "Ignored without validation when design_enabled is false."
    return {
        "effect_type": runtime(
            required=False,
            has_default=True,
            default="odds_ratio",
            omission="Uses the odds_ratio registry entry.",
            null_accepted=False,
            explicit_null="Rejected as an unsupported effect registry key.",
        ),
        "estimate": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Infers the point estimate from the CI midpoint on the working scale.",
            null_accepted=True,
            explicit_null="Same as omission: infer from the CI.",
        ),
        "lower": runtime(
            required=True,
            has_default=False,
            default=None,
            omission="Rejected because both CI limits are runtime-required.",
            null_accepted=False,
            explicit_null="Rejected because both CI limits are runtime-required.",
        ),
        "upper": runtime(
            required=True,
            has_default=False,
            default=None,
            omission="Rejected because both CI limits are runtime-required.",
            null_accepted=False,
            explicit_null="Rejected because both CI limits are runtime-required.",
        ),
        "null_value": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Uses the selected effect registry default null.",
            null_accepted=True,
            explicit_null="Same as omission: use the effect registry default null.",
        ),
        "thresholds": runtime(
            required=False,
            has_default=True,
            default=[],
            omission="Uses no reference thresholds.",
            null_accepted=True,
            explicit_null="Same as omission: use no reference thresholds.",
        ),
        "display_range_lower": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Uses the automatically constructed observed x-grid.",
            null_accepted=True,
            explicit_null="Treated as absent; both bounds must otherwise be supplied together.",
        ),
        "display_range_upper": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Uses the automatically constructed observed x-grid.",
            null_accepted=True,
            explicit_null="Treated as absent; both bounds must otherwise be supplied together.",
        ),
        "display_natural_axis": runtime(
            required=False,
            has_default=True,
            default=True,
            omission="Requests a natural display axis for ratio measures.",
            null_accepted=True,
            explicit_null="Boolean coercion selects the working-scale display axis.",
        ),
        "grid_points": runtime(
            required=False,
            has_default=True,
            default=801,
            omission="Uses 801 grid points.",
            null_accepted=False,
            explicit_null="Rejected by integer coercion.",
        ),
        "show_cutoffs": runtime(
            required=False,
            has_default=True,
            default=True,
            omission="Enables compatibility-guide overlays.",
            null_accepted=True,
            explicit_null="Boolean coercion disables compatibility-guide overlays.",
        ),
        "design_enabled": runtime(
            required=False,
            has_default=True,
            default=False,
            omission="Returns null for the design response block.",
            null_accepted=True,
            explicit_null="Boolean coercion disables design and ignores all other design fields.",
        ),
        "design_alpha": runtime(
            required=False,
            has_default=True,
            default=0.05,
            omission="Uses alpha 0.05 when design is enabled.",
            null_accepted=True,
            explicit_null="Same as omission when design is enabled; otherwise ignored.",
        ),
        "design_selection_rule": runtime(
            required=False,
            has_default=True,
            default="two_sided_p_lt_alpha",
            omission="Uses the two-sided p-value rule when design is enabled.",
            null_accepted=False,
            explicit_null=f"Rejected when design is enabled. {ignored}",
        ),
        "design_claim_direction": runtime(
            required=False,
            has_default=True,
            default="positive",
            omission="Uses the positive direction unless a one-sided rule fixes direction.",
            null_accepted=False,
            explicit_null=f"Rejected when evaluated by a design rule. {ignored}",
        ),
        "design_claim_threshold": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Uses no threshold; threshold-conditioned rules reject its absence.",
            null_accepted=True,
            explicit_null=f"Same as omission when design is enabled. {ignored}",
        ),
        "design_information_multiplier": runtime(
            required=False,
            has_default=True,
            default=1.0,
            omission="Uses current CI-implied information when design is enabled.",
            null_accepted=True,
            explicit_null=f"Same as omission when design is enabled. {ignored}",
        ),
        "design_precision_target_effect": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Produces no inverse-precision target rows.",
            null_accepted=True,
            explicit_null=f"Same as omission when design is enabled. {ignored}",
        ),
        "design_target_power": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Uses 0.80 only when a precision target effect is supplied.",
            null_accepted=True,
            explicit_null=f"Same as omission when design is enabled. {ignored}",
        ),
        "design_max_type_s": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Adds no maximum Type S inverse-precision target.",
            null_accepted=True,
            explicit_null=f"Same as omission when design is enabled. {ignored}",
        ),
        "design_max_type_m": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Adds no maximum Type M inverse-precision target.",
            null_accepted=True,
            explicit_null=f"Same as omission when design is enabled. {ignored}",
        ),
        "design_true_effects": runtime(
            required=False,
            has_default=True,
            default=[],
            omission="Adds no custom true-effect scenarios.",
            null_accepted=True,
            explicit_null=f"Same as omission when design is enabled. {ignored}",
        ),
        "design_plausible_range_lower": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Uses no design-only plausible-range overlay.",
            null_accepted=True,
            explicit_null=f"Treated as absent; both bounds must otherwise be supplied. {ignored}",
        ),
        "design_plausible_range_upper": runtime(
            required=False,
            has_default=True,
            default=None,
            omission="Uses no design-only plausible-range overlay.",
            null_accepted=True,
            explicit_null=f"Treated as absent; both bounds must otherwise be supplied. {ignored}",
        ),
    }


def _browser_contract_schema() -> dict[str, Any]:
    orders = _browser_key_order()
    request_order = [
        "effect_type",
        "estimate",
        "lower",
        "upper",
        "null_value",
        "thresholds",
        "display_range_lower",
        "display_range_upper",
        "display_natural_axis",
        "grid_points",
        "show_cutoffs",
        "design_enabled",
        "design_alpha",
        "design_selection_rule",
        "design_claim_direction",
        "design_claim_threshold",
        "design_information_multiplier",
        "design_precision_target_effect",
        "design_target_power",
        "design_max_type_s",
        "design_max_type_m",
        "design_true_effects",
        "design_plausible_range_lower",
        "design_plausible_range_upper",
    ]
    objects = {
        "CurveRequest": {
            "field_order": request_order,
            "order_contract": "TypedDict declaration order; input mapping order is not relied upon",
            "typed_dict_total": False,
            "required_fields": ["lower", "upper"],
            "optional_fields": [
                field for field in request_order if field not in {"lower", "upper"}
            ],
            "fields": {
                "effect_type": _field(
                    "string",
                    nullable=False,
                    units="effect registry key",
                    meaning="Selects effect family, working scale, label, and default null",
                    conditioning="shared input",
                ),
                "estimate": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Optional point estimate used only to validate the CI midpoint",
                    conditioning="observed evidence",
                ),
                "lower": _field(
                    "number",
                    nullable=False,
                    units="natural effect scale",
                    meaning="Reported 95% CI lower limit",
                    conditioning="observed evidence",
                ),
                "upper": _field(
                    "number",
                    nullable=False,
                    units="natural effect scale",
                    meaning="Reported 95% CI upper limit",
                    conditioning="observed evidence",
                ),
                "null_value": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Candidate null; defaults from the effect registry",
                    conditioning="shared observed/design reference",
                ),
                "thresholds": _field(
                    "number[]",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Observed reference thresholds or MCIDs",
                    conditioning="observed evidence",
                ),
                "display_range_lower": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Optional presentation-only x-grid lower bound",
                    conditioning="presentation",
                ),
                "display_range_upper": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Optional presentation-only x-grid upper bound",
                    conditioning="presentation",
                ),
                "display_natural_axis": _field(
                    "boolean",
                    nullable=True,
                    units="display mode",
                    meaning="Requests natural-scale rather than working-scale x values",
                    conditioning="presentation",
                ),
                "grid_points": _field(
                    "integer",
                    nullable=False,
                    units="count",
                    meaning="Requested grid size, normalized to an odd count",
                    conditioning="shared grid",
                ),
                "show_cutoffs": _field(
                    "boolean",
                    nullable=True,
                    units="display flag",
                    meaning="Controls compatibility-guide overlays",
                    conditioning="presentation",
                ),
                "design_enabled": _field(
                    "boolean",
                    nullable=True,
                    units="mode flag",
                    meaning="Enables repeated-study design calibration",
                    conditioning="design",
                ),
                "design_alpha": _field(
                    "number",
                    nullable=True,
                    units="probability",
                    meaning="Selected-claim rule alpha",
                    conditioning="design",
                ),
                "design_selection_rule": _field(
                    "string",
                    nullable=False,
                    units="selection-rule key",
                    meaning="One of the six supported selected-claim rules",
                    conditioning="design",
                ),
                "design_claim_direction": _field(
                    "string",
                    nullable=False,
                    units="positive or negative",
                    meaning="Direction used by directional selected-claim rules",
                    conditioning="design",
                ),
                "design_claim_threshold": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Threshold used only by threshold-conditioned claim rules",
                    conditioning="design",
                ),
                "design_information_multiplier": _field(
                    "number",
                    nullable=True,
                    units="information ratio",
                    meaning="Scales hypothetical design SE by the inverse square root",
                    conditioning="design",
                ),
                "design_precision_target_effect": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Assumed true effect for inverse precision targets",
                    conditioning="design",
                ),
                "design_target_power": _field(
                    "number",
                    nullable=True,
                    units="probability",
                    meaning="Requested selected-claim probability target",
                    conditioning="design",
                ),
                "design_max_type_s": _field(
                    "number",
                    nullable=True,
                    units="conditional probability",
                    meaning="Optional maximum Type S target",
                    conditioning="design",
                ),
                "design_max_type_m": _field(
                    "number",
                    nullable=True,
                    units="working-scale magnitude ratio",
                    meaning="Optional maximum Type M target",
                    conditioning="design",
                ),
                "design_true_effects": _field(
                    "number[]",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Custom assumed true-effect scenario values",
                    conditioning="design",
                ),
                "design_plausible_range_lower": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Optional design-panel-only true-effect range lower bound",
                    conditioning="design presentation",
                ),
                "design_plausible_range_upper": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Optional design-panel-only true-effect range upper bound",
                    conditioning="design presentation",
                ),
            },
        },
        "CurveResponse": {
            "field_order": orders["$"],
            "order_contract": "frozen browser response insertion order",
            "fields": {
                "meta": _field(
                    "MetaPayload",
                    nullable=False,
                    units="mixed metadata",
                    meaning="Effect, reconstruction, threshold, range, and S-2 metadata",
                    conditioning="observed evidence",
                ),
                "summary": _field(
                    "SummaryPayload",
                    nullable=False,
                    units="mixed summary values",
                    meaning="Observed reconstructed summary statistics",
                    conditioning="observed evidence",
                ),
                "warnings": _field(
                    "string[]",
                    nullable=False,
                    units="messages",
                    meaning="Observed reconstruction and finite-value warnings",
                    conditioning="observed evidence",
                ),
                "grid": _field(
                    "GridPayload",
                    nullable=False,
                    units="aligned arrays",
                    meaning="Observed x-grid and function values",
                    conditioning="observed evidence",
                ),
                "design": _field(
                    "DesignPayload",
                    nullable=True,
                    units="mixed design values",
                    meaning="Repeated-study design block; null when disabled",
                    conditioning="design",
                ),
            },
        },
        "EffectSpecPayload": {
            "field_order": orders["$.meta.effect_spec"],
            "order_contract": "deterministic dataclass field order",
            "fields": {
                "key": _field(
                    "string",
                    nullable=False,
                    units="registry key",
                    meaning="Canonical effect-measure key",
                    conditioning="shared metadata",
                ),
                "label": _field(
                    "string",
                    nullable=False,
                    units="display text",
                    meaning="Human-readable effect label",
                    conditioning="shared metadata",
                ),
                "family": _field(
                    "string",
                    nullable=False,
                    units="additive or ratio",
                    meaning="Effect family",
                    conditioning="shared metadata",
                ),
                "working_scale": _field(
                    "string",
                    nullable=False,
                    units="identity or log",
                    meaning="Numerical working scale",
                    conditioning="shared metadata",
                ),
                "default_null": _field(
                    "number",
                    nullable=False,
                    units="natural effect scale",
                    meaning="Registry default null value",
                    conditioning="shared metadata",
                ),
                "positive_only": _field(
                    "boolean",
                    nullable=False,
                    units="constraint flag",
                    meaning="Whether natural-scale inputs must be positive",
                    conditioning="shared metadata",
                ),
            },
        },
        "MetaPayload": {
            "field_order": orders["$.meta"],
            "order_contract": "frozen browser response insertion order",
            "fields": {
                "effect_spec": _field(
                    "EffectSpecPayload",
                    nullable=False,
                    units="registry metadata",
                    meaning="Selected effect specification",
                    conditioning="observed evidence",
                ),
                "display_axis_scale": _field(
                    "string",
                    nullable=False,
                    units="natural or working",
                    meaning="Scale of effect_display values",
                    conditioning="presentation",
                ),
                "estimate_source": _field(
                    "string",
                    nullable=False,
                    units="source label",
                    meaning="Whether an estimate was inferred or supplied and validated",
                    conditioning="observed evidence",
                ),
                "default_null_applied": _field(
                    "boolean",
                    nullable=False,
                    units="flag",
                    meaning="Whether the effect-registry null was applied",
                    conditioning="observed evidence",
                ),
                "grid_points": _field(
                    "integer",
                    nullable=False,
                    units="count",
                    meaning="Actual odd grid size",
                    conditioning="shared grid",
                ),
                "show_cutoffs": _field(
                    "boolean",
                    nullable=False,
                    units="display flag",
                    meaning="Whether compatibility guide cutoffs are requested",
                    conditioning="presentation",
                ),
                "se_method": _field(
                    "string",
                    nullable=False,
                    units="method label",
                    meaning="CI-width or mean-side SE reconstruction method",
                    conditioning="observed evidence",
                ),
                "relative_asymmetry": _field(
                    "number",
                    nullable=False,
                    units="relative difference",
                    meaning="Relative CI-side SE asymmetry",
                    conditioning="observed evidence",
                ),
                "thresholds_display": _field(
                    "number[]",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Reference thresholds for display",
                    conditioning="observed evidence",
                ),
                "thresholds_working": _field(
                    "number[]",
                    nullable=False,
                    units="working effect scale",
                    meaning="Reference thresholds used in calculations",
                    conditioning="observed evidence",
                ),
                "display_range_active": _field(
                    "boolean",
                    nullable=False,
                    units="flag",
                    meaning="Whether an explicit presentation window is active",
                    conditioning="presentation",
                ),
                "display_range_display": _field(
                    "number[2]",
                    nullable=True,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Requested displayed x-grid endpoints",
                    conditioning="presentation",
                ),
                "display_range_working": _field(
                    "number[2]",
                    nullable=True,
                    units="working effect scale",
                    meaning="Requested x-grid endpoints used to build the grid",
                    conditioning="presentation",
                ),
                "threshold_support_summaries": _field(
                    "ThresholdSupportPayload[]",
                    nullable=False,
                    units="mixed support values",
                    meaning="Observed support summaries in input threshold order",
                    conditioning="observed evidence",
                ),
                "s_minus_2_interval": _field(
                    "SMinus2IntervalPayload",
                    nullable=False,
                    units="support interval",
                    meaning="Effects with log relative support at least -2",
                    conditioning="observed evidence",
                ),
            },
        },
        "ThresholdSupportPayload": {
            "field_order": orders["$.meta.threshold_support_summaries[]"],
            "order_contract": "frozen browser response insertion order",
            "fields": {
                "threshold_display": _field(
                    "number",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Reference threshold for display",
                    conditioning="observed evidence",
                ),
                "threshold_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Reference threshold used in calculations",
                    conditioning="observed evidence",
                ),
                "relative_likelihood": _field(
                    "number",
                    nullable=False,
                    units="ratio to peak",
                    meaning="Normalized Wald relative likelihood at the threshold",
                    conditioning="observed evidence",
                ),
                "log_relative_likelihood": _field(
                    "number",
                    nullable=False,
                    units="natural log ratio to peak",
                    meaning="Log normalized Wald relative likelihood",
                    conditioning="observed evidence",
                ),
                "likelihood_ratio_mle_to_threshold": _field(
                    "number",
                    nullable=True,
                    units="support ratio",
                    meaning="Exponentiated MLE-to-threshold support when finite",
                    conditioning="observed evidence",
                ),
                "log_likelihood_ratio_mle_to_threshold": _field(
                    "number",
                    nullable=False,
                    units="natural log support ratio",
                    meaning="Log MLE-to-threshold support",
                    conditioning="observed evidence",
                ),
                "likelihood_ratio_threshold_to_null": _field(
                    "number",
                    nullable=True,
                    units="support ratio",
                    meaning="Exponentiated threshold-to-null support when finite",
                    conditioning="observed evidence",
                ),
                "log_likelihood_ratio_threshold_to_null": _field(
                    "number",
                    nullable=True,
                    units="natural log support ratio",
                    meaning="Log threshold-to-null support when the null summary is finite",
                    conditioning="observed evidence",
                ),
                "direction_from_estimate": _field(
                    "string",
                    nullable=False,
                    units="direction label",
                    meaning="Threshold position relative to the CI-implied estimate",
                    conditioning="observed evidence",
                ),
                "direction_from_null": _field(
                    "string",
                    nullable=False,
                    units="direction label",
                    meaning="Threshold position relative to the null",
                    conditioning="observed evidence",
                ),
            },
        },
        "SMinus2IntervalPayload": {
            "field_order": orders["$.meta.s_minus_2_interval"],
            "order_contract": "frozen browser response insertion order",
            "fields": {
                "support_cutoff": _field(
                    "number",
                    nullable=False,
                    units="log relative support",
                    meaning="Fixed log support cutoff of -2",
                    conditioning="observed evidence",
                ),
                "relative_likelihood_cutoff": _field(
                    "number",
                    nullable=False,
                    units="ratio to peak",
                    meaning="Exponentiated support cutoff exp(-2)",
                    conditioning="observed evidence",
                ),
                "likelihood_ratio_mle_to_bound": _field(
                    "number",
                    nullable=False,
                    units="support ratio",
                    meaning="Peak-to-bound ratio exp(2)",
                    conditioning="observed evidence",
                ),
                "range_display": _field(
                    "number[2]",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Finite display-scale support endpoints",
                    conditioning="observed evidence",
                ),
                "range_working": _field(
                    "number[2]",
                    nullable=False,
                    units="working effect scale",
                    meaning="Finite estimate plus or minus 2 SE endpoints",
                    conditioning="observed evidence",
                ),
            },
        },
        "SummaryPayload": {
            "field_order": orders["$.summary"],
            "order_contract": "frozen browser response insertion order",
            "fields": {
                "estimate_display": _field(
                    "number",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="CI-midpoint estimate for display",
                    conditioning="observed evidence",
                ),
                "estimate_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="CI-midpoint estimate used in calculations",
                    conditioning="observed evidence",
                ),
                "ci_display": _field(
                    "number[2]",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Reported CI limits",
                    conditioning="observed evidence",
                ),
                "ci_working": _field(
                    "number[2]",
                    nullable=False,
                    units="working effect scale",
                    meaning="Reported CI limits after transformation",
                    conditioning="observed evidence",
                ),
                "null_display": _field(
                    "number",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Null value for display",
                    conditioning="observed evidence",
                ),
                "null_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Null value used in calculations",
                    conditioning="shared observed/design reference",
                ),
                "working_scale_se": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="SE reconstructed from the reported 95% CI",
                    conditioning="shared precision",
                ),
                "null_relative_likelihood": _field(
                    "number",
                    nullable=False,
                    units="ratio to peak",
                    meaning="Normalized Wald relative likelihood at the null",
                    conditioning="observed evidence",
                ),
                "log_null_relative_likelihood": _field(
                    "number",
                    nullable=True,
                    units="natural log ratio to peak",
                    meaning="Log relative likelihood at the null when finite",
                    conditioning="observed evidence",
                ),
                "likelihood_ratio_mle_to_null": _field(
                    "number",
                    nullable=True,
                    units="support ratio",
                    meaning="Exponentiated MLE-to-null support when finite",
                    conditioning="observed evidence",
                ),
                "log_likelihood_ratio_mle_to_null": _field(
                    "number",
                    nullable=True,
                    units="natural log support ratio",
                    meaning="Log MLE-to-null support when finite",
                    conditioning="observed evidence",
                ),
                "two_sided_wald_p_value": _field(
                    "number",
                    nullable=False,
                    units="probability",
                    meaning="Two-sided compatibility value at the null",
                    conditioning="observed evidence",
                ),
                "null_z_value": _field(
                    "number",
                    nullable=True,
                    units="standard errors",
                    meaning="Signed standardized null distance when finite",
                    conditioning="observed evidence",
                ),
                "critical_effect_markers_display": _field(
                    "number[2]",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Legacy paired 80% benchmark markers for display",
                    conditioning="design interpretation",
                ),
                "critical_effect_markers_working": _field(
                    "number[2]",
                    nullable=False,
                    units="working effect scale",
                    meaning="Legacy paired 80% benchmark markers",
                    conditioning="design interpretation",
                ),
                "critical_effect_distance_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Legacy z-sum benchmark distance from the null",
                    conditioning="design interpretation",
                ),
            },
        },
        "GridPayload": {
            "field_order": orders["$.grid"],
            "order_contract": "frozen order used by CSV export and tests",
            "fields": {
                "effect_display": _field(
                    "number[]",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Displayed candidate effects",
                    conditioning="observed evidence",
                ),
                "effect_working": _field(
                    "number[]",
                    nullable=False,
                    units="working effect scale",
                    meaning="Candidate effects used in calculations",
                    conditioning="observed evidence",
                ),
                "z": _field(
                    "number[]",
                    nullable=False,
                    units="standard errors",
                    meaning="Standardized distances from the CI-implied estimate",
                    conditioning="observed evidence",
                ),
                "compatibility": _field(
                    "number[]",
                    nullable=False,
                    units="two-sided probability",
                    meaning="Wald compatibility curve values",
                    conditioning="observed evidence",
                ),
                "relative_likelihood": _field(
                    "number[]",
                    nullable=False,
                    units="ratio to peak",
                    meaning="Normalized Wald relative-likelihood values",
                    conditioning="observed evidence",
                ),
                "log_relative_likelihood": _field(
                    "number[]",
                    nullable=False,
                    units="natural log ratio to peak",
                    meaning="Log normalized Wald relative-likelihood values",
                    conditioning="observed evidence",
                ),
            },
        },
        "DesignPayload": {
            "field_order": orders["$.design"],
            "order_contract": "frozen browser response insertion order",
            "fields": {
                "config": _field(
                    "DesignConfigPayload",
                    nullable=False,
                    units="mixed configuration",
                    meaning="Resolved design inputs and precision",
                    conditioning="design",
                ),
                "grid": _field(
                    "DesignGridPayload",
                    nullable=False,
                    units="aligned arrays",
                    meaning="Forward operating characteristics on the shared x-grid",
                    conditioning="design",
                ),
                "scenarios": _field(
                    "DesignScenarioPayload[]",
                    nullable=False,
                    units="scenario rows",
                    meaning="Deduplicated null, estimate, threshold, and custom scenarios",
                    conditioning="design",
                ),
                "precision_targets": _field(
                    "DesignPrecisionTargetPayload[]",
                    nullable=False,
                    units="inverse precision rows",
                    meaning="Per-target required precision results",
                    conditioning="design",
                ),
                "warnings": _field(
                    "string[]",
                    nullable=False,
                    units="messages",
                    meaning="Design conditioning, semantics, and feasibility notes",
                    conditioning="design",
                ),
            },
        },
        "DesignConfigPayload": {
            "field_order": orders["$.design.config"],
            "order_contract": "frozen browser response insertion order",
            "fields": {
                "enabled": _field(
                    "boolean",
                    nullable=False,
                    units="flag",
                    meaning="Design block enabled state",
                    conditioning="design",
                ),
                "alpha": _field(
                    "number",
                    nullable=False,
                    units="probability",
                    meaning="Resolved selected-claim alpha",
                    conditioning="design",
                ),
                "selection_rule": _field(
                    "string",
                    nullable=False,
                    units="selection-rule key",
                    meaning="Resolved selected-claim rule",
                    conditioning="design",
                ),
                "selection_rule_label": _field(
                    "string",
                    nullable=False,
                    units="display text",
                    meaning="Human-readable selected-claim rule",
                    conditioning="design",
                ),
                "claim_direction": _field(
                    "string",
                    nullable=False,
                    units="positive or negative",
                    meaning="Resolved claim direction",
                    conditioning="design",
                ),
                "claim_threshold_display": _field(
                    "number",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Directional claim threshold for display",
                    conditioning="design",
                ),
                "claim_threshold_working": _field(
                    "number",
                    nullable=True,
                    units="working effect scale",
                    meaning="Directional claim threshold used in tail calculations",
                    conditioning="design",
                ),
                "se_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Compatibility alias for design SE",
                    conditioning="design",
                ),
                "current_se_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="SE reconstructed from the current CI",
                    conditioning="shared precision",
                ),
                "design_se_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Hypothetical SE after information scaling",
                    conditioning="design",
                ),
                "information_multiplier": _field(
                    "number",
                    nullable=False,
                    units="information ratio",
                    meaning="Hypothetical information relative to current precision",
                    conditioning="design",
                ),
                "current_ci_width_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Approximate current 95% CI width",
                    conditioning="shared precision",
                ),
                "approx_design_ci_width_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Approximate design 95% CI width",
                    conditioning="design",
                ),
                "null_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Null used for true-effect distances",
                    conditioning="design",
                ),
                "estimate_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Observed CI-implied estimate used only for observed exaggeration",
                    conditioning="design comparison",
                ),
                "near_null_delta": _field(
                    "number",
                    nullable=False,
                    units="standardized distance",
                    meaning="Tolerance for undefined Type S/M ratios",
                    conditioning="design",
                ),
                "type_m_scale_note": _field(
                    "string",
                    nullable=False,
                    units="interpretive text",
                    meaning="States additive or log-working-scale Type M semantics",
                    conditioning="design",
                ),
                "plausible_range_display": _field(
                    "number[2]",
                    nullable=True,
                    units="natural effect scale",
                    meaning="Optional displayed true-effect range",
                    conditioning="design presentation",
                ),
                "plausible_range_working": _field(
                    "number[2]",
                    nullable=True,
                    units="working effect scale",
                    meaning="Optional transformed true-effect range",
                    conditioning="design presentation",
                ),
            },
        },
        "DesignGridPayload": {
            "field_order": orders["$.design.grid"],
            "order_contract": "frozen browser response and CSV alignment order",
            "fields": {
                "true_effect_display": _field(
                    "number[]",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Each x value treated as assumed truth",
                    conditioning="design",
                ),
                "true_effect_working": _field(
                    "number[]",
                    nullable=False,
                    units="working effect scale",
                    meaning="Assumed truths used in calculations",
                    conditioning="design",
                ),
                "delta": _field(
                    "number[]",
                    nullable=False,
                    units="design standard errors",
                    meaning="True-effect distances from the null",
                    conditioning="design",
                ),
                "power": _field(
                    "number[]",
                    nullable=False,
                    units="selected-claim probability",
                    meaning="Probability that the selected-claim rule is met",
                    conditioning="design",
                ),
                "type_s": _field(
                    "(number|null)[]",
                    nullable=False,
                    units="conditional probability",
                    meaning="Wrong-sign probability among selected claims",
                    conditioning="design",
                ),
                "type_m": _field(
                    "(number|null)[]",
                    nullable=False,
                    units="working-scale magnitude ratio",
                    meaning="Expected selected magnitude divided by true magnitude",
                    conditioning="design",
                ),
                "expected_selected_abs_z": _field(
                    "(number|null)[]",
                    nullable=False,
                    units="absolute Z",
                    meaning="Expected selected absolute Wald Z",
                    conditioning="design",
                ),
                "observed_exaggeration": _field(
                    "(number|null)[]",
                    nullable=False,
                    units="working-scale magnitude ratio",
                    meaning="Observed-to-assumed-true magnitude ratio",
                    conditioning="design comparison",
                ),
            },
        },
        "DesignScenarioPayload": {
            "field_order": orders["$.design.scenarios[]"],
            "order_contract": "frozen row key order; row order follows source priority",
            "fields": {
                "label": _field(
                    "string",
                    nullable=False,
                    units="display text",
                    meaning="Scenario label",
                    conditioning="design",
                ),
                "source": _field(
                    "string",
                    nullable=False,
                    units="source key",
                    meaning="Null, estimate, threshold, or custom source",
                    conditioning="design",
                ),
                "true_effect_display": _field(
                    "number",
                    nullable=False,
                    units="display effect scale; see meta.display_axis_scale",
                    meaning="Assumed truth for display",
                    conditioning="design",
                ),
                "true_effect_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Assumed truth used in calculations",
                    conditioning="design",
                ),
                "delta": _field(
                    "number",
                    nullable=False,
                    units="design standard errors",
                    meaning="True-effect distance from the null",
                    conditioning="design",
                ),
                "power": _field(
                    "number",
                    nullable=False,
                    units="selected-claim probability",
                    meaning="Probability that the selection rule is met",
                    conditioning="design",
                ),
                "type_s": _field(
                    "number",
                    nullable=True,
                    units="conditional probability",
                    meaning="Wrong-sign probability among selected claims",
                    conditioning="design",
                ),
                "type_m": _field(
                    "number",
                    nullable=True,
                    units="working-scale magnitude ratio",
                    meaning="Expected selected magnitude exaggeration",
                    conditioning="design",
                ),
                "observed_exaggeration": _field(
                    "number",
                    nullable=True,
                    units="working-scale magnitude ratio",
                    meaning="Observed-to-assumed-true magnitude ratio",
                    conditioning="design comparison",
                ),
                "note": _field(
                    "string",
                    nullable=True,
                    units="interpretive text",
                    meaning="Scenario caveat or source note",
                    conditioning="design",
                ),
            },
        },
        "DesignPrecisionTargetPayload": {
            "field_order": orders["$.design.precision_targets[]"],
            "order_contract": "frozen row key and requested-target order",
            "fields": {
                "target": _field(
                    "string",
                    nullable=False,
                    units="target label",
                    meaning="Power, maximum Type S, or maximum Type M",
                    conditioning="design",
                ),
                "requested_value": _field(
                    "number",
                    nullable=False,
                    units="target-specific",
                    meaning="Requested target or maximum",
                    conditioning="design",
                ),
                "target_effect_display": _field(
                    "number",
                    nullable=False,
                    units="natural effect scale",
                    meaning="Assumed true effect as supplied before working-scale transformation",
                    conditioning="design",
                ),
                "target_effect_working": _field(
                    "number",
                    nullable=False,
                    units="working effect scale",
                    meaning="Assumed true effect used by the solver",
                    conditioning="design",
                ),
                "required_se": _field(
                    "number",
                    nullable=True,
                    units="working effect scale",
                    meaning="Largest SE estimated to satisfy the target",
                    conditioning="design",
                ),
                "required_information_multiplier": _field(
                    "number",
                    nullable=True,
                    units="information ratio",
                    meaning="Current SE squared over required SE squared",
                    conditioning="design",
                ),
                "approx_95_ci_width_working": _field(
                    "number",
                    nullable=True,
                    units="working effect scale",
                    meaning="Approximate 2 z0.975 required-SE width",
                    conditioning="design",
                ),
                "achieved_power": _field(
                    "number",
                    nullable=True,
                    units="selected-claim probability",
                    meaning="Power at the solved SE",
                    conditioning="design",
                ),
                "achieved_type_s": _field(
                    "number",
                    nullable=True,
                    units="conditional probability",
                    meaning="Type S at the solved SE",
                    conditioning="design",
                ),
                "achieved_type_m": _field(
                    "number",
                    nullable=True,
                    units="working-scale magnitude ratio",
                    meaning="Type M at the solved SE",
                    conditioning="design",
                ),
                "note": _field(
                    "string",
                    nullable=False,
                    units="status text",
                    meaning="Already met, bisection, undefined, or infeasible status",
                    conditioning="design",
                ),
            },
        },
    }
    request_runtime = _request_runtime_contract()
    if set(request_runtime) != set(request_order):
        raise AssertionError("CurveRequest runtime metadata must cover every request field")
    for field_name, runtime_metadata in request_runtime.items():
        objects["CurveRequest"]["fields"][field_name].update(runtime_metadata)

    return {
        "schema_version": 1,
        "source_commit": SOURCE_COMMIT,
        "strict_json": {
            "allow_nan": False,
            "undefined_value": None,
            "status": "enforced for every successful response",
            "known_defect": None,
        },
        "objects": objects,
        "ordering": {
            "response_key_orders_are_frozen": True,
            "request_mapping_order_is_ignored": True,
            "separate_order_fixture": "browser_key_order.json",
        },
    }


def _browser_key_order() -> dict[str, list[str]]:
    return {
        "$": ["meta", "summary", "warnings", "grid", "design"],
        "$.meta": [
            "effect_spec",
            "display_axis_scale",
            "estimate_source",
            "default_null_applied",
            "grid_points",
            "show_cutoffs",
            "se_method",
            "relative_asymmetry",
            "thresholds_display",
            "thresholds_working",
            "display_range_active",
            "display_range_display",
            "display_range_working",
            "threshold_support_summaries",
            "s_minus_2_interval",
        ],
        "$.meta.effect_spec": [
            "key",
            "label",
            "family",
            "working_scale",
            "default_null",
            "positive_only",
        ],
        "$.meta.threshold_support_summaries[]": [
            "threshold_display",
            "threshold_working",
            "relative_likelihood",
            "log_relative_likelihood",
            "likelihood_ratio_mle_to_threshold",
            "log_likelihood_ratio_mle_to_threshold",
            "likelihood_ratio_threshold_to_null",
            "log_likelihood_ratio_threshold_to_null",
            "direction_from_estimate",
            "direction_from_null",
        ],
        "$.meta.s_minus_2_interval": [
            "support_cutoff",
            "relative_likelihood_cutoff",
            "likelihood_ratio_mle_to_bound",
            "range_display",
            "range_working",
        ],
        "$.summary": [
            "estimate_display",
            "estimate_working",
            "ci_display",
            "ci_working",
            "null_display",
            "null_working",
            "working_scale_se",
            "null_relative_likelihood",
            "log_null_relative_likelihood",
            "likelihood_ratio_mle_to_null",
            "log_likelihood_ratio_mle_to_null",
            "two_sided_wald_p_value",
            "null_z_value",
            "critical_effect_markers_display",
            "critical_effect_markers_working",
            "critical_effect_distance_working",
        ],
        "$.grid": [
            "effect_display",
            "effect_working",
            "z",
            "compatibility",
            "relative_likelihood",
            "log_relative_likelihood",
        ],
        "$.design": ["config", "grid", "scenarios", "precision_targets", "warnings"],
        "$.design.config": [
            "enabled",
            "alpha",
            "selection_rule",
            "selection_rule_label",
            "claim_direction",
            "claim_threshold_display",
            "claim_threshold_working",
            "se_working",
            "current_se_working",
            "design_se_working",
            "information_multiplier",
            "current_ci_width_working",
            "approx_design_ci_width_working",
            "null_working",
            "estimate_working",
            "near_null_delta",
            "type_m_scale_note",
            "plausible_range_display",
            "plausible_range_working",
        ],
        "$.design.grid": [
            "true_effect_display",
            "true_effect_working",
            "delta",
            "power",
            "type_s",
            "type_m",
            "expected_selected_abs_z",
            "observed_exaggeration",
        ],
        "$.design.scenarios[]": [
            "label",
            "source",
            "true_effect_display",
            "true_effect_working",
            "delta",
            "power",
            "type_s",
            "type_m",
            "observed_exaggeration",
            "note",
        ],
        "$.design.precision_targets[]": [
            "target",
            "requested_value",
            "target_effect_display",
            "target_effect_working",
            "required_se",
            "required_information_multiplier",
            "approx_95_ci_width_working",
            "achieved_power",
            "achieved_type_s",
            "achieved_type_m",
            "note",
        ],
    }


def _export_schemas() -> dict[str, Any]:
    observed_columns = [
        "effect_display",
        "effect_working",
        "z",
        "compatibility",
        "relative_likelihood",
        "log_relative_likelihood",
    ]
    design_columns = [
        "design_selection_rule",
        "design_claim_direction",
        "design_information_multiplier",
        "design_claim_threshold_working",
        "design_delta_if_true",
        "design_power_if_true",
        "design_type_s_if_true",
        "design_type_m_if_true",
        "design_expected_selected_abs_z_if_true",
        "design_observed_exaggeration_if_true",
    ]
    return {
        "browser_contract.json": _browser_contract_schema(),
        "browser_key_order.json": _browser_key_order(),
        "effect_registry.json": {
            "schema_version": 1,
            "source_commit": SOURCE_COMMIT,
            "key_order": list(EFFECT_SPECS),
            "specs": [asdict(spec) for spec in EFFECT_SPECS.values()],
        },
        "csv_columns.json": {
            "schema_version": 1,
            "observed_only": observed_columns,
            "design_enabled": observed_columns + design_columns,
        },
        "figure_exports.json": {
            "schema_version": 1,
            "dashboard": {
                "width": 1400,
                "height_observed": 1100,
                "height_design": 1600,
                "scale": 2,
                "format": "png",
            },
            "manuscript": {
                "width": 1400,
                "height_observed": 1000,
                "height_design": 1500,
                "scale": 2,
                "format": "png",
                "caption_embedded": False,
            },
            "controls": [
                "export-csv",
                "export-png",
                "export-manuscript-png",
                "copy-caption",
                "copy-reviewer-text",
            ],
        },
    }


def build_artifacts() -> dict[Path, str]:
    versions = _dependency_versions()
    artifacts: dict[Path, str] = {}
    manifest_cases: list[dict[str, Any]] = []
    fixture_hash_inputs: list[str] = []

    for case in _cases():
        request_path = Path("requests") / f"{case.case_id}.json"
        response_path = Path("responses") / f"{case.case_id}.json"
        expected = _evaluate_case(case)
        request_text = _canonical_json(case.request)
        response_text = _canonical_json(expected)
        request_sha = _sha256_text(request_text)
        response_sha = _sha256_text(response_text)
        fixture_sha = _sha256_text(_canonical_json({"request": case.request, "expected": expected}))
        artifacts[request_path] = request_text
        artifacts[response_path] = response_text
        fixture_hash_inputs.append(f"{case.case_id}:{fixture_sha}")
        manifest_cases.append(
            {
                "id": case.case_id,
                "matrix_case": case.matrix_case,
                "description": case.description,
                "fixture_kind": case.fixture_kind,
                "expected_status": expected["status"],
                "request_file": request_path.as_posix(),
                "expected_file": response_path.as_posix(),
                "request_sha256": request_sha,
                "expected_sha256": response_sha,
                "fixture_sha256": fixture_sha,
                "source_commit": SOURCE_COMMIT,
                "versions": versions,
                "tolerance": {"rtol": RTOL, "atol": ATOL},
                "exact_float_paths": list(EXACT_FLOAT_PATHS),
            }
        )

    manifest_schemas: list[dict[str, str]] = []
    for filename, schema in _export_schemas().items():
        path = Path("export_schemas") / filename
        schema_text = _canonical_json(schema)
        schema_sha = _sha256_text(schema_text)
        artifacts[path] = schema_text
        fixture_hash_inputs.append(f"{path.as_posix()}:{schema_sha}")
        manifest_schemas.append({"path": path.as_posix(), "sha256": schema_sha})

    fixture_set_sha = _sha256_text("\n".join(fixture_hash_inputs) + "\n")
    manifest = {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "generated_on": BASELINE_DATE,
        "source": {
            "repository": SOURCE_REPOSITORY,
            "branch": SOURCE_BRANCH,
            "commit": SOURCE_COMMIT,
        },
        "serialization": {
            "encoding": "UTF-8",
            "sorted_keys": True,
            "indent": 2,
            "newline": "LF with terminal newline",
            "allow_nan": False,
        },
        "default_tolerance": {"rtol": RTOL, "atol": ATOL},
        "comparison": {
            "float_mode": "tolerant except for declared exact_float_paths",
            "exact_float_paths": list(EXACT_FLOAT_PATHS),
        },
        "versions": versions,
        "dependency_authority_files": list(DEPENDENCY_AUTHORITY_FILES),
        "case_count": len(manifest_cases),
        "cases": manifest_cases,
        "export_schemas": manifest_schemas,
        "fixture_set_sha256": fixture_set_sha,
    }
    artifacts[Path("manifest.json")] = _canonical_json(manifest)
    return artifacts


def _dirty_paths() -> list[str]:
    output = _run_git("status", "--porcelain", "--untracked-files=all")
    return [line for line in output.splitlines() if line]


def _validate_write_source(*, allow_dirty: bool) -> None:
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_COMMIT, "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
    )
    protected_diff = _run_git(
        "diff",
        "--name-only",
        SOURCE_COMMIT,
        "--",
        "src/confcurve",
        "web",
        *DEPENDENCY_AUTHORITY_FILES,
    )
    if protected_diff:
        raise SystemExit(
            "Refusing to regenerate the frozen baseline after production or "
            "dependency-authority changes:\n"
            f"{protected_diff}"
        )
    dirty = _dirty_paths()
    if dirty and not allow_dirty:
        raise SystemExit(
            "Refusing to write from a dirty worktree. Review the paths and rerun with "
            "--allow-dirty only for the intentional baseline implementation:\n" + "\n".join(dirty)
        )


def write_artifacts(*, force: bool, allow_dirty: bool) -> None:
    _validate_write_source(allow_dirty=allow_dirty)
    artifacts = build_artifacts()
    existing = [
        GOLDEN_ROOT / relative for relative in artifacts if (GOLDEN_ROOT / relative).exists()
    ]
    if existing and not force:
        paths = "\n".join(str(path.relative_to(PROJECT_ROOT)) for path in existing[:10])
        raise SystemExit(
            "Refusing to overwrite existing golden artifacts without --force:\n" + paths
        )

    expected_paths = {GOLDEN_ROOT / relative for relative in artifacts}
    if force:
        for directory in (REQUESTS_ROOT, RESPONSES_ROOT, SCHEMAS_ROOT):
            if directory.exists():
                for path in directory.glob("*.json"):
                    if path not in expected_paths:
                        path.unlink()

    for relative, content in artifacts.items():
        destination = GOLDEN_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")

    print(f"Wrote {len(artifacts)} deterministic artifacts under {GOLDEN_ROOT}")


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _manifest_structure_mismatches(manifest: Any) -> list[str]:
    if not isinstance(manifest, dict):
        return ["manifest: expected an object"]

    mismatches: list[str] = []
    expected_top_level = {
        "schema_version",
        "generated_on",
        "source",
        "serialization",
        "default_tolerance",
        "comparison",
        "versions",
        "dependency_authority_files",
        "case_count",
        "cases",
        "export_schemas",
        "fixture_set_sha256",
    }
    actual_top_level = set(manifest)
    for key in sorted(expected_top_level - actual_top_level):
        mismatches.append(f"manifest.{key}: missing key")
    for key in sorted(actual_top_level - expected_top_level):
        mismatches.append(f"manifest.{key}: unexpected key")
    if mismatches:
        return mismatches

    expected_static = {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "generated_on": BASELINE_DATE,
        "source": {
            "repository": SOURCE_REPOSITORY,
            "branch": SOURCE_BRANCH,
            "commit": SOURCE_COMMIT,
        },
        "serialization": {
            "encoding": "UTF-8",
            "sorted_keys": True,
            "indent": 2,
            "newline": "LF with terminal newline",
            "allow_nan": False,
        },
        "default_tolerance": {"rtol": RTOL, "atol": ATOL},
        "comparison": {
            "float_mode": "tolerant except for declared exact_float_paths",
            "exact_float_paths": list(EXACT_FLOAT_PATHS),
        },
        "dependency_authority_files": list(DEPENDENCY_AUTHORITY_FILES),
    }
    for key, expected_value in expected_static.items():
        if manifest.get(key) != expected_value:
            mismatches.append(
                f"manifest.{key}: expected {expected_value!r}, observed {manifest.get(key)!r}"
            )
    mismatches.extend(
        _dependency_version_mismatches(
            manifest.get("versions"),
            path="manifest.versions",
        )
    )

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        mismatches.append("manifest.cases: expected an array")
        cases = []
    expected_cases = list(_cases())
    if manifest.get("case_count") != len(cases):
        mismatches.append(
            "manifest.case_count: expected to equal the number of recorded case entries"
        )
    if len(cases) != len(expected_cases):
        mismatches.append(
            f"manifest.cases: expected {len(expected_cases)} entries, observed {len(cases)}"
        )

    case_keys = {
        "id",
        "matrix_case",
        "description",
        "fixture_kind",
        "expected_status",
        "request_file",
        "expected_file",
        "request_sha256",
        "expected_sha256",
        "fixture_sha256",
        "source_commit",
        "versions",
        "tolerance",
        "exact_float_paths",
    }
    for index, (record, case) in enumerate(zip(cases, expected_cases, strict=False)):
        record_path = f"manifest.cases[{index}]"
        if not isinstance(record, dict):
            mismatches.append(f"{record_path}: expected an object")
            continue
        if set(record) != case_keys:
            missing = sorted(case_keys - set(record))
            unexpected = sorted(set(record) - case_keys)
            if missing:
                mismatches.append(f"{record_path}: missing keys {missing!r}")
            if unexpected:
                mismatches.append(f"{record_path}: unexpected keys {unexpected!r}")
        expected_record_static = {
            "id": case.case_id,
            "matrix_case": case.matrix_case,
            "description": case.description,
            "fixture_kind": case.fixture_kind,
            "expected_status": ("error" if case.fixture_kind == "expected_error" else "success"),
            "request_file": f"requests/{case.case_id}.json",
            "expected_file": f"responses/{case.case_id}.json",
            "source_commit": SOURCE_COMMIT,
            "versions": manifest.get("versions"),
            "tolerance": {"rtol": RTOL, "atol": ATOL},
            "exact_float_paths": list(EXACT_FLOAT_PATHS),
        }
        for key, expected_value in expected_record_static.items():
            if record.get(key) != expected_value:
                mismatches.append(
                    f"{record_path}.{key}: expected {expected_value!r}, "
                    f"observed {record.get(key)!r}"
                )
        for key in ("request_sha256", "expected_sha256", "fixture_sha256"):
            if not _is_sha256(record.get(key)):
                mismatches.append(f"{record_path}.{key}: expected lowercase SHA256")

    schemas = manifest.get("export_schemas")
    if not isinstance(schemas, list):
        mismatches.append("manifest.export_schemas: expected an array")
        schemas = []
    expected_schema_paths = [f"export_schemas/{filename}" for filename in _export_schemas()]
    if len(schemas) != len(expected_schema_paths):
        mismatches.append("manifest.export_schemas: expected one entry for every generated schema")
    for index, (record, expected_path) in enumerate(
        zip(schemas, expected_schema_paths, strict=False)
    ):
        record_path = f"manifest.export_schemas[{index}]"
        if not isinstance(record, dict):
            mismatches.append(f"{record_path}: expected an object")
            continue
        if set(record) != {"path", "sha256"}:
            mismatches.append(f"{record_path}: expected only path and sha256 keys")
        if record.get("path") != expected_path:
            mismatches.append(
                f"{record_path}.path: expected {expected_path!r}, observed {record.get('path')!r}"
            )
        if not _is_sha256(record.get("sha256")):
            mismatches.append(f"{record_path}.sha256: expected lowercase SHA256")
    if not _is_sha256(manifest.get("fixture_set_sha256")):
        mismatches.append("manifest.fixture_set_sha256: expected lowercase SHA256")
    return mismatches


def check_artifacts() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Golden baseline check failed:\nmissing {MANIFEST_PATH}")
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    mismatches: list[str] = []
    if manifest_text != _canonical_json(manifest):
        mismatches.append("manifest.json: content is not canonical sorted/indented JSON")
    mismatches.extend(_manifest_structure_mismatches(manifest))
    if not mismatches:
        try:
            mismatches.extend(_verify_stored_hashes(manifest))
        except FileNotFoundError as exc:
            mismatches.append(f"missing {Path(exc.filename).relative_to(PROJECT_ROOT)}")
    if mismatches:
        raise SystemExit("Golden baseline check failed:\n" + "\n".join(mismatches))

    expected_cases = {case.case_id: case for case in _cases()}
    recorded_cases = {case["id"]: case for case in manifest.get("cases", [])}
    for case_id in sorted(expected_cases.keys() - recorded_cases.keys()):
        mismatches.append(f"manifest missing case {case_id}")
    for case_id in sorted(recorded_cases.keys() - expected_cases.keys()):
        mismatches.append(f"manifest has unexpected case {case_id}")
    versions = manifest["versions"]
    for case_id, case in expected_cases.items():
        record = recorded_cases.get(case_id)
        if record is None:
            continue
        expected_request = _canonical_json(case.request)
        request_path = GOLDEN_ROOT / record["request_file"]
        if not request_path.exists():
            mismatches.append(f"missing {request_path.relative_to(PROJECT_ROOT)}")
        elif request_path.read_text(encoding="utf-8") != expected_request:
            mismatches.append(f"{case_id}: stored request differs from the case definition")
        expected_static = {
            "matrix_case": case.matrix_case,
            "description": case.description,
            "fixture_kind": case.fixture_kind,
            "expected_status": ("error" if case.fixture_kind == "expected_error" else "success"),
            "source_commit": SOURCE_COMMIT,
            "versions": versions,
            "tolerance": {"rtol": RTOL, "atol": ATOL},
            "exact_float_paths": list(EXACT_FLOAT_PATHS),
        }
        for key, value in expected_static.items():
            if record.get(key) != value:
                mismatches.append(
                    f"{case_id}.{key}: expected {value!r}, observed {record.get(key)!r}"
                )

    expected_schemas = _export_schemas()
    expected_schema_paths = {SCHEMAS_ROOT / filename for filename in expected_schemas}
    for filename, schema in expected_schemas.items():
        path = SCHEMAS_ROOT / filename
        expected_text = _canonical_json(schema)
        if not path.exists():
            mismatches.append(f"missing {path.relative_to(PROJECT_ROOT)}")
        elif path.read_text(encoding="utf-8") != expected_text:
            mismatches.append(f"stale {path.relative_to(PROJECT_ROOT)}")

    expected_paths = {
        MANIFEST_PATH,
        *(GOLDEN_ROOT / record["request_file"] for record in recorded_cases.values()),
        *(GOLDEN_ROOT / record["expected_file"] for record in recorded_cases.values()),
        *expected_schema_paths,
    }
    for directory in (REQUESTS_ROOT, RESPONSES_ROOT, SCHEMAS_ROOT):
        if directory.exists():
            for path in directory.glob("*.json"):
                if path not in expected_paths:
                    mismatches.append(f"unexpected {path.relative_to(PROJECT_ROOT)}")

    if mismatches:
        raise SystemExit("Golden baseline check failed:\n" + "\n".join(mismatches))
    compare_baseline()
    print(
        f"Golden baseline integrity and definitions pass for {len(recorded_cases)} cases; "
        "floating-point behavior was compared with declared tolerances"
    )


def compare_values(
    expected: Any,
    actual: Any,
    *,
    path: str = "$",
    rtol: float = RTOL,
    atol: float = ATOL,
    exact_float_paths: frozenset[str] = frozenset(),
) -> list[str]:
    mismatches: list[str] = []
    if expected is None or actual is None:
        if expected is not actual:
            mismatches.append(f"{path}: expected {expected!r}, observed {actual!r}")
        return mismatches
    if isinstance(expected, bool) or isinstance(actual, bool):
        if type(expected) is not type(actual) or expected != actual:
            mismatches.append(
                f"{path}: expected {expected!r} ({type(expected).__name__}), "
                f"observed {actual!r} ({type(actual).__name__})"
            )
        return mismatches
    if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
            return [f"{path}: expected object, observed {type(actual).__name__}"]
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            mismatches.append(f"{path}.{key}: missing key")
        for key in sorted(actual_keys - expected_keys):
            mismatches.append(f"{path}.{key}: unexpected key")
        for key in expected:
            if key in actual:
                mismatches.extend(
                    compare_values(
                        expected[key],
                        actual[key],
                        path=f"{path}.{key}",
                        rtol=rtol,
                        atol=atol,
                        exact_float_paths=exact_float_paths,
                    )
                )
        return mismatches
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected array, observed {type(actual).__name__}"]
        if len(expected) != len(actual):
            mismatches.append(
                f"{path}: expected array length {len(expected)}, observed {len(actual)}"
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual, strict=False)):
            mismatches.extend(
                compare_values(
                    expected_item,
                    actual_item,
                    path=f"{path}[{index}]",
                    rtol=rtol,
                    atol=atol,
                    exact_float_paths=exact_float_paths,
                )
            )
        return mismatches
    if isinstance(expected, float):
        if not isinstance(actual, float):
            return [
                f"{path}: expected float {expected!r}, "
                f"observed {actual!r} ({type(actual).__name__})"
            ]
        if path in exact_float_paths and expected != actual:
            mismatches.append(
                f"{path}: expected exact float {expected:.17g}, observed {actual:.17g}"
            )
        elif path not in exact_float_paths and not math.isclose(
            expected,
            actual,
            rel_tol=rtol,
            abs_tol=atol,
        ):
            mismatches.append(
                f"{path}: expected {expected:.17g}, observed {actual:.17g} "
                f"(rtol={rtol:g}, atol={atol:g})"
            )
        return mismatches
    if isinstance(expected, int):
        if type(actual) is not int or expected != actual:
            mismatches.append(
                f"{path}: expected integer {expected!r}, "
                f"observed {actual!r} ({type(actual).__name__})"
            )
        return mismatches
    if type(expected) is not type(actual) or expected != actual:
        mismatches.append(
            f"{path}: expected {expected!r} ({type(expected).__name__}), "
            f"observed {actual!r} ({type(actual).__name__})"
        )
    return mismatches


def _contract_values(response: dict[str, Any], path: str) -> list[tuple[str, Any]]:
    if path == "$":
        return [("$", response)]
    values: list[tuple[str, Any]] = [("$", response)]
    for component in path.removeprefix("$.").split("."):
        if not component:
            continue
        repeated = component.endswith("[]")
        key = component[:-2] if repeated else component
        next_values: list[tuple[str, Any]] = []
        for resolved_path, current in values:
            if current is None or not isinstance(current, Mapping) or key not in current:
                continue
            child = current[key]
            child_path = f"{resolved_path}.{key}"
            if repeated:
                if not isinstance(child, list):
                    next_values.append((child_path, child))
                    continue
                next_values.extend(
                    (f"{child_path}[{index}]", item) for index, item in enumerate(child)
                )
            else:
                next_values.append((child_path, child))
        values = next_values
    return values


def _compare_key_order(response: dict[str, Any], orders: dict[str, list[str]]) -> list[str]:
    mismatches: list[str] = []
    for path, expected_keys in orders.items():
        for resolved_path, value in _contract_values(response, path):
            if value is None:
                continue
            if not isinstance(value, Mapping):
                mismatches.append(
                    f"{resolved_path}: expected an object for key-order comparison, "
                    f"observed {type(value).__name__}"
                )
                continue
            actual_keys = list(value)
            if actual_keys != expected_keys:
                mismatches.append(
                    f"{resolved_path}: expected key order {expected_keys!r}, "
                    f"observed {actual_keys!r}"
                )
    return mismatches


def _verify_stored_hashes(manifest: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    fixture_hash_inputs: list[str] = []
    for case in manifest["cases"]:
        request_path = GOLDEN_ROOT / case["request_file"]
        expected_path = GOLDEN_ROOT / case["expected_file"]
        request_text = request_path.read_text(encoding="utf-8")
        expected_text = expected_path.read_text(encoding="utf-8")
        observed_request_sha = _sha256_text(request_text)
        observed_expected_sha = _sha256_text(expected_text)
        request = json.loads(request_text)
        expected = json.loads(expected_text)
        if request_text != _canonical_json(request):
            mismatches.append(f"{case['id']}: request is not canonical JSON")
        if expected_text != _canonical_json(expected):
            mismatches.append(f"{case['id']}: expected response is not canonical JSON")
        if expected.get("status") != case["expected_status"]:
            mismatches.append(
                f"{case['id']}: expected_status {case['expected_status']!r} "
                f"does not match stored response status {expected.get('status')!r}"
            )
        observed_fixture_sha = _sha256_text(
            _canonical_json({"request": request, "expected": expected})
        )
        if observed_request_sha != case["request_sha256"]:
            mismatches.append(f"{case['id']}: request SHA256 mismatch")
        if observed_expected_sha != case["expected_sha256"]:
            mismatches.append(f"{case['id']}: expected SHA256 mismatch")
        if observed_fixture_sha != case["fixture_sha256"]:
            mismatches.append(f"{case['id']}: combined fixture SHA256 mismatch")
        fixture_hash_inputs.append(f"{case['id']}:{observed_fixture_sha}")
    for schema in manifest["export_schemas"]:
        path = GOLDEN_ROOT / schema["path"]
        schema_text = path.read_text(encoding="utf-8")
        schema_value = json.loads(schema_text)
        if schema_text != _canonical_json(schema_value):
            mismatches.append(f"{schema['path']}: schema is not canonical JSON")
        observed_sha = _sha256_text(schema_text)
        if observed_sha != schema["sha256"]:
            mismatches.append(f"{schema['path']}: SHA256 mismatch")
        fixture_hash_inputs.append(f"{schema['path']}:{observed_sha}")
    observed_set_sha = _sha256_text("\n".join(fixture_hash_inputs) + "\n")
    if observed_set_sha != manifest["fixture_set_sha256"]:
        mismatches.append("fixture_set_sha256: mismatch")
    return mismatches


def compare_baseline(*, case_filter: set[str] | None = None) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    mismatches = _verify_stored_hashes(manifest)
    orders = json.loads((SCHEMAS_ROOT / "browser_key_order.json").read_text(encoding="utf-8"))
    case_map = {case.case_id: case for case in _cases()}
    compared = 0
    for case_record in manifest["cases"]:
        case_id = case_record["id"]
        if case_filter is not None and case_id not in case_filter:
            continue
        case = case_map[case_id]
        expected = json.loads(
            (GOLDEN_ROOT / case_record["expected_file"]).read_text(encoding="utf-8")
        )
        actual = _evaluate_case(case)
        json.dumps(actual, allow_nan=False)
        tolerance = case_record["tolerance"]
        case_mismatches = compare_values(
            expected,
            actual,
            path="$",
            rtol=tolerance["rtol"],
            atol=tolerance["atol"],
            exact_float_paths=frozenset(case_record["exact_float_paths"]),
        )
        mismatches.extend(f"{case_id}{message.removeprefix('$')}" for message in case_mismatches)
        if actual["status"] == "success":
            full_response = compute_curves(case.request)
            mismatches.extend(
                f"{case_id}{message.removeprefix('$')}"
                for message in _compare_key_order(full_response, orders)
            )
        compared += 1
    if case_filter:
        missing = case_filter - set(case_map)
        mismatches.extend(f"unknown requested case: {case_id}" for case_id in sorted(missing))
    if mismatches:
        preview = "\n".join(f"- {message}" for message in mismatches[:100])
        remainder = len(mismatches) - min(len(mismatches), 100)
        suffix = f"\n- ... {remainder} additional mismatches" if remainder else ""
        raise SystemExit(f"Golden baseline comparison failed:\n{preview}{suffix}")
    print(f"Golden baseline comparison passed for {compared} cases (rtol={RTOL:g}, atol={ATOL:g})")


def generator_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate or check the frozen golden baseline")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write deterministic artifacts")
    mode.add_argument("--check", action="store_true", help="check artifacts (default)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow intentional replacement of existing generated artifacts",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow the intentional milestone implementation worktree when writing",
    )
    args = parser.parse_args(argv)
    if args.force and not args.write:
        parser.error("--force is valid only with --write")
    if args.allow_dirty and not args.write:
        parser.error("--allow-dirty is valid only with --write")
    if args.write:
        write_artifacts(force=args.force, allow_dirty=args.allow_dirty)
    else:
        check_artifacts()


def comparator_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Compare current behavior with golden fixtures")
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="compare only a case ID; repeat to select multiple cases",
    )
    args = parser.parse_args(argv)
    compare_baseline(case_filter=set(args.case) or None)
