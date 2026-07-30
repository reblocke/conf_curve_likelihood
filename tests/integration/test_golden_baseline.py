from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm

import golden_baseline as baseline
from confcurve import models
from confcurve.core import Z975, confidence_curve, relative_likelihood
from confcurve.design import design_metrics_for_true_effects
from confcurve.models import EFFECT_SPECS
from confcurve.web_contract import compute_curves
from golden_baseline import (
    ATOL,
    DEPENDENCY_AUTHORITY_FILES,
    EXACT_FLOAT_PATHS,
    GOLDEN_ROOT,
    RTOL,
    _canonical_json,
    _compare_key_order,
    _manifest_structure_mismatches,
    check_artifacts,
    compare_baseline,
    compare_values,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _expected(case_id: str) -> dict:
    return json.loads((GOLDEN_ROOT / "responses" / f"{case_id}.json").read_text())


def _response(case_id: str) -> dict:
    expected = _expected(case_id)
    assert expected["status"] == "success"
    return expected["response"]


def test_generated_golden_artifacts_are_current() -> None:
    check_artifacts()


def test_recursive_golden_comparator_passes() -> None:
    compare_baseline()


def test_recursive_comparator_reports_readable_paths_and_strict_types() -> None:
    mismatches = compare_values(
        {"summary": {"estimate": 0.42, "count": 1, "defined": None}},
        {"summary": {"estimate": 0.5, "count": 1.0, "defined": 0}},
    )

    assert any("$.summary.estimate" in mismatch for mismatch in mismatches)
    assert any("$.summary.count" in mismatch for mismatch in mismatches)
    assert any("$.summary.defined" in mismatch for mismatch in mismatches)


def test_recursive_comparator_uses_exact_float_paths_for_registry_identity() -> None:
    expected = {"response": {"meta": {"effect_spec": {"default_null": 1.0}}}}
    actual = copy.deepcopy(expected)
    actual["response"]["meta"]["effect_spec"]["default_null"] = math.nextafter(1.0, 2.0)

    assert compare_values(expected, actual) == []
    mismatches = compare_values(
        expected,
        actual,
        exact_float_paths=frozenset(EXACT_FLOAT_PATHS),
    )

    assert len(mismatches) == 1
    assert "$.response.meta.effect_spec.default_null" in mismatches[0]
    assert "exact float" in mismatches[0]


def test_recursive_comparator_rejects_missing_and_unexpected_keys() -> None:
    mismatches = compare_values({"meta": {"required": True}}, {"meta": {"extra": True}})

    assert "$.meta.required: missing key" in mismatches
    assert "$.meta.extra: unexpected key" in mismatches


def test_writer_refuses_silent_fixture_overwrite_without_touching_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    golden_root = tmp_path / "golden"
    golden_root.mkdir()
    (golden_root / "manifest.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(baseline, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(baseline, "GOLDEN_ROOT", golden_root)
    monkeypatch.setattr(baseline, "REQUESTS_ROOT", golden_root / "requests")
    monkeypatch.setattr(baseline, "RESPONSES_ROOT", golden_root / "responses")
    monkeypatch.setattr(baseline, "SCHEMAS_ROOT", golden_root / "export_schemas")
    monkeypatch.setattr(baseline, "MANIFEST_PATH", golden_root / "manifest.json")
    monkeypatch.setattr(baseline, "_validate_write_source", lambda **_: None)
    monkeypatch.setattr(
        baseline,
        "build_artifacts",
        lambda: {Path("manifest.json"): "{}\n"},
    )

    with pytest.raises(SystemExit, match="without --force"):
        baseline.write_artifacts(force=False, allow_dirty=True)


def test_writer_preflight_protects_dependency_authority_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(baseline.subprocess, "run", lambda *args, **kwargs: None)
    calls: list[tuple[str, ...]] = []

    def fake_run_git(*args: str) -> str:
        calls.append(args)
        if args[:3] == ("diff", "--name-only", baseline.SOURCE_COMMIT):
            return "pyproject.toml"
        return ""

    monkeypatch.setattr(baseline, "_run_git", fake_run_git)

    with pytest.raises(SystemExit, match="dependency-authority"):
        baseline._validate_write_source(allow_dirty=True)

    diff_call = next(call for call in calls if call[0] == "diff")
    assert set(DEPENDENCY_AUTHORITY_FILES) <= set(diff_call)


def test_manifest_covers_all_matrix_cases_and_required_subcases() -> None:
    manifest = json.loads((GOLDEN_ROOT / "manifest.json").read_text())
    matrix_cases = {case["matrix_case"] for case in manifest["cases"]}
    case_ids = {case["id"] for case in manifest["cases"]}

    assert matrix_cases == {f"B0{number}" for number in range(1, 9)}
    assert {
        "B07a-null",
        "B07b-near-null",
        "B07c-threshold-infeasible",
        "B07d-alpha-zero",
        "B07e-alpha-one",
        "B07f-alpha-nonnumeric",
        "B07g-alpha-underflow",
        "B07h-display-range-pair",
        "B07i-design-range-pair",
        "B07j-ratio-positive",
        "B07k-disabled-design-ignored",
    } <= case_ids
    assert {
        "B08a-additive-midpoint",
        "B08b-s-minus-2-clipping",
        "B08c-log-likelihood-fallback",
        "B08d-ratio-natural-clipping",
        "B08e-unrepresentable-design-distance",
    } <= case_ids
    assert manifest["default_tolerance"] == {"rtol": RTOL, "atol": ATOL}
    assert manifest["comparison"]["exact_float_paths"] == list(EXACT_FLOAT_PATHS)
    assert manifest["dependency_authority_files"] == list(DEPENDENCY_AUTHORITY_FILES)
    assert (
        manifest["versions"]["python_declared"]
        == (PROJECT_ROOT / ".python-version").read_text(encoding="utf-8").strip()
    )
    assert (
        manifest["versions"]["python_runtime"].split(".")[:2]
        == manifest["versions"]["python_declared"].split(".")[:2]
    )
    assert all(
        case["expected_status"]
        == ("error" if case["fixture_kind"] == "expected_error" else "success")
        for case in manifest["cases"]
    )


def test_manifest_static_structure_rejects_tampered_expected_status() -> None:
    manifest = json.loads((GOLDEN_ROOT / "manifest.json").read_text())
    assert _manifest_structure_mismatches(manifest) == []

    tampered = copy.deepcopy(manifest)
    tampered["cases"][0]["expected_status"] = "error"
    mismatches = _manifest_structure_mismatches(tampered)

    assert any("manifest.cases[0].expected_status" in mismatch for mismatch in mismatches)


def test_manifest_preserves_historical_adapter_version_as_fixture_provenance() -> None:
    manifest = json.loads((GOLDEN_ROOT / "manifest.json").read_text())

    assert baseline._dependency_versions()["confcurve"] == "0.2.4"
    assert baseline._fixture_versions()["confcurve"] == "0.1.0"
    assert manifest["versions"]["confcurve"] == "0.1.0"
    assert all(case["versions"]["confcurve"] == "0.1.0" for case in manifest["cases"])
    assert _manifest_structure_mismatches(manifest) == []

    tampered = copy.deepcopy(manifest)
    tampered["versions"]["confcurve"] = "0.1.1"
    mismatches = _manifest_structure_mismatches(tampered)

    assert "manifest.versions.confcurve: expected '0.1.0', observed '0.1.1'" in mismatches


def test_manifest_accepts_a_different_patch_within_declared_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = json.loads((GOLDEN_ROOT / "manifest.json").read_text())
    current_versions = copy.deepcopy(manifest["versions"])
    current_versions["python_runtime"] = "3.11.99"
    monkeypatch.setattr(baseline, "_dependency_versions", lambda: current_versions)

    assert _manifest_structure_mismatches(manifest) == []


def test_all_stored_json_is_strict_and_canonical() -> None:
    for path in sorted(GOLDEN_ROOT.rglob("*.json")):
        text = path.read_text(encoding="utf-8")
        value = json.loads(text)
        json.dumps(value, allow_nan=False)
        assert text == _canonical_json(value), path


def test_machine_contract_schema_covers_every_typed_payload_field() -> None:
    schema = json.loads((GOLDEN_ROOT / "export_schemas" / "browser_contract.json").read_text())
    typed_payloads = {
        name: getattr(models, name)
        for name in (
            "CurveRequest",
            "CurveResponse",
            "MetaPayload",
            "ThresholdSupportPayload",
            "SMinus2IntervalPayload",
            "SummaryPayload",
            "GridPayload",
            "DesignPayload",
            "DesignConfigPayload",
            "DesignGridPayload",
            "DesignScenarioPayload",
            "DesignPrecisionTargetPayload",
        )
    }
    for name, payload_type in typed_payloads.items():
        declared_fields = list(payload_type.__annotations__)
        assert schema["objects"][name]["field_order"] == declared_fields
        assert set(schema["objects"][name]["fields"]) == set(declared_fields)

    effect_fields = list(models.EffectSpec.__dataclass_fields__)
    assert schema["objects"]["EffectSpecPayload"]["field_order"] == effect_fields
    assert set(schema["objects"]["EffectSpecPayload"]["fields"]) == set(effect_fields)


def test_machine_contract_schema_records_field_semantics_and_runtime_request_rules() -> None:
    schema = json.loads((GOLDEN_ROOT / "export_schemas" / "browser_contract.json").read_text())
    objects = schema["objects"]
    required_field_metadata = {
        "type",
        "nullable",
        "units_or_scale",
        "meaning",
        "conditioning",
    }
    for object_schema in objects.values():
        for field in object_schema["fields"].values():
            assert required_field_metadata <= set(field)

    request = objects["CurveRequest"]
    assert request["typed_dict_total"] is False
    assert request["required_fields"] == ["lower", "upper"]
    assert set(request["optional_fields"]) == set(request["field_order"]) - {"lower", "upper"}
    runtime_metadata = {
        "required",
        "has_omission_default",
        "omission_default",
        "omission_behavior",
        "explicit_null_accepted",
        "explicit_null_behavior",
    }
    assert all(runtime_metadata <= set(field) for field in request["fields"].values())
    assert request["fields"]["lower"]["required"] is True
    assert request["fields"]["lower"]["explicit_null_accepted"] is False
    assert request["fields"]["null_value"]["nullable"] is True
    assert request["fields"]["null_value"]["explicit_null_accepted"] is True
    assert request["fields"]["thresholds"]["omission_default"] == []
    assert request["fields"]["design_enabled"]["omission_default"] is False

    assert request["fields"]["thresholds"]["units_or_scale"] == "natural effect scale"
    assert (
        objects["MetaPayload"]["fields"]["thresholds_display"]["units_or_scale"]
        == "display effect scale; see meta.display_axis_scale"
    )
    assert (
        objects["DesignPrecisionTargetPayload"]["fields"]["target_effect_display"]["units_or_scale"]
        == "natural effect scale"
    )

    orders = json.loads((GOLDEN_ROOT / "export_schemas" / "browser_key_order.json").read_text())
    assert orders["$.meta.effect_spec"] == list(models.EffectSpec.__dataclass_fields__)


def test_effect_registry_schema_freezes_every_key_and_default_exactly() -> None:
    registry = json.loads((GOLDEN_ROOT / "export_schemas" / "effect_registry.json").read_text())

    assert registry["key_order"] == list(EFFECT_SPECS)
    assert registry["specs"] == [
        {
            "key": spec.key,
            "label": spec.label,
            "family": spec.family,
            "working_scale": spec.working_scale,
            "default_null": spec.default_null,
            "positive_only": spec.positive_only,
        }
        for spec in EFFECT_SPECS.values()
    ]


def test_key_order_comparator_checks_every_repeated_row() -> None:
    response = {
        "design": {
            "scenarios": [
                {"first": 1, "second": 2},
                {"second": 2, "first": 1},
            ]
        }
    }

    mismatches = _compare_key_order(
        response,
        {"$.design.scenarios[]": ["first", "second"]},
    )

    assert len(mismatches) == 1
    assert "$.design.scenarios[1]" in mismatches[0]


def test_b01_additive_reconstruction_invariants() -> None:
    response = _response("B01")

    assert response["summary"]["estimate_display"] == pytest.approx(0.42)
    assert response["summary"]["estimate_working"] == pytest.approx(0.42)
    assert response["summary"]["ci_display"] == pytest.approx([0.11, 0.73])
    assert response["summary"]["ci_working"] == pytest.approx([0.11, 0.73])
    assert response["grid"]["effect_display"] == response["grid"]["effect_working"]
    assert max(response["grid"]["compatibility"]) == pytest.approx(1.0)
    ci_endpoints = np.asarray(response["summary"]["ci_working"])
    assert confidence_curve(
        ci_endpoints,
        theta_hat=response["summary"]["estimate_working"],
        se=response["summary"]["working_scale_se"],
    ) == pytest.approx([0.05, 0.05])
    assert relative_likelihood(
        ci_endpoints,
        theta_hat=response["summary"]["estimate_working"],
        se=response["summary"]["working_scale_se"],
    ) == pytest.approx([math.exp(-0.5 * Z975**2)] * 2)
    threshold = response["meta"]["threshold_support_summaries"][0]
    expected_log_support = (
        -0.5
        * (
            (threshold["threshold_working"] - response["summary"]["estimate_working"])
            / response["summary"]["working_scale_se"]
        )
        ** 2
    )
    assert threshold["log_relative_likelihood"] == pytest.approx(expected_log_support)
    assert threshold["relative_likelihood"] == pytest.approx(math.exp(expected_log_support))
    assert response["summary"]["critical_effect_distance_working"] > 0
    assert len(response["grid"]["effect_display"]) == 401


def test_b02_ratio_and_b03_display_window_invariants() -> None:
    ratio = _response("B02")
    window = _response("B03")

    assert ratio["summary"]["estimate_display"] == pytest.approx(math.sqrt(1.2 * 2.7))
    assert ratio["summary"]["estimate_working"] == pytest.approx(math.log(1.8))
    interval = ratio["meta"]["s_minus_2_interval"]
    estimate = ratio["summary"]["estimate_working"]
    se = ratio["summary"]["working_scale_se"]
    assert interval["range_working"] == pytest.approx([estimate - 2 * se, estimate + 2 * se])
    assert all(value > 0 for value in ratio["grid"]["effect_display"])

    assert window["grid"]["effect_display"][0] == pytest.approx(0.9)
    assert window["grid"]["effect_display"][-1] == pytest.approx(1.1)
    assert compare_values(ratio["summary"], window["summary"]) == []
    assert (
        compare_values(
            ratio["meta"]["threshold_support_summaries"],
            window["meta"]["threshold_support_summaries"],
        )
        == []
    )
    assert {
        "The chosen display range excludes the point estimate.",
        "The chosen display range excludes the lower 95% CI bound.",
        "The chosen display range excludes the upper 95% CI bound.",
        "The chosen display range excludes one or more reference thresholds / MCIDs.",
        "The chosen display range excludes one or more critical-effect markers.",
    } <= set(window["warnings"])
    assert "The chosen display range excludes the null value." not in window["warnings"]


def test_b04_and_b05_forward_design_invariants() -> None:
    additive = _response("B04")
    ratio = _response("B05")

    null_scenario = next(
        scenario for scenario in additive["design"]["scenarios"] if scenario["source"] == "null"
    )
    assert null_scenario["power"] == pytest.approx(0.05)
    assert null_scenario["type_s"] is None
    assert null_scenario["type_m"] is None
    assert null_scenario["observed_exaggeration"] is None
    scenario_values = [
        scenario["true_effect_working"] for scenario in additive["design"]["scenarios"]
    ]
    assert len(scenario_values) == len(set(scenario_values))
    symmetric_metrics = design_metrics_for_true_effects(
        [-0.3, 0.3],
        null_working=additive["design"]["config"]["null_working"],
        se=additive["design"]["config"]["design_se_working"],
        estimate_working=additive["design"]["config"]["estimate_working"],
        alpha=additive["design"]["config"]["alpha"],
        selection_rule=additive["design"]["config"]["selection_rule"],
    )
    negative, positive = symmetric_metrics
    assert negative.power == pytest.approx(positive.power)
    assert negative.type_s == pytest.approx(positive.type_s)
    assert negative.type_m == pytest.approx(positive.type_m)
    assert negative.expected_selected_abs_z == pytest.approx(positive.expected_selected_abs_z)

    config = ratio["design"]["config"]
    assert config["claim_threshold_working"] == pytest.approx(math.log(1.25))
    assert config["design_se_working"] == pytest.approx(config["current_se_working"] / 2)
    assert ratio["summary"]["working_scale_se"] == pytest.approx(
        _response("B02")["summary"]["working_scale_se"]
    )
    assert "log scale" in config["type_m_scale_note"]

    scenario = next(
        row
        for row in ratio["design"]["scenarios"]
        if row["source"] == "custom_true_effect"
        and row["true_effect_display"] == pytest.approx(1.5)
    )
    critical_z = norm.isf(config["alpha"] / 2.0)
    tail_boundary = (config["claim_threshold_working"] - config["null_working"]) / config[
        "design_se_working"
    ] + critical_z
    scenario_delta = (scenario["true_effect_working"] - config["null_working"]) / config[
        "design_se_working"
    ]
    assert scenario["power"] == pytest.approx(norm.sf(tail_boundary - scenario_delta))

    observed_only = compute_curves(
        {
            "effect_type": "odds_ratio",
            "lower": 1.2,
            "upper": 2.7,
            "design_enabled": False,
            "grid_points": 401,
        }
    )
    for key in ("meta", "summary", "warnings", "grid"):
        assert compare_values(ratio[key], observed_only[key]) == []
    assert observed_only["design"] is None


def test_b06_precision_target_order_and_identities() -> None:
    response = _response("B06")
    rows = response["design"]["precision_targets"]

    assert [row["target"] for row in rows] == [
        "Power",
        "Maximum Type S",
        "Maximum Type M",
    ]
    current_se = response["design"]["config"]["current_se_working"]
    for row in rows:
        assert row["required_se"] is not None
        assert row["required_information_multiplier"] == pytest.approx(
            (current_se / row["required_se"]) ** 2
        )
        assert row["approx_95_ci_width_working"] == pytest.approx(
            2 * 1.959963984540054 * row["required_se"]
        )
    strictest = min(rows, key=lambda row: row["required_se"])
    assert strictest["required_information_multiplier"] == max(
        row["required_information_multiplier"] for row in rows
    )
    by_target = {row["target"]: row for row in rows}
    assert by_target["Power"]["achieved_power"] >= by_target["Power"]["requested_value"]
    assert (
        by_target["Maximum Type S"]["achieved_type_s"]
        <= by_target["Maximum Type S"]["requested_value"]
    )
    assert (
        by_target["Maximum Type M"]["achieved_type_m"]
        <= by_target["Maximum Type M"]["requested_value"]
    )


def test_b07_undefined_infeasible_and_invalid_outcomes() -> None:
    for case_id in ("B07a-null", "B07b-near-null", "B07c-threshold-infeasible"):
        response = _response(case_id)
        [row] = response["design"]["precision_targets"]
        assert row["required_se"] is None
        assert row["required_information_multiplier"] is None
        assert row["note"]

    for case_id in (
        "B07d-alpha-zero",
        "B07e-alpha-one",
        "B07f-alpha-nonnumeric",
        "B07g-alpha-underflow",
        "B07h-display-range-pair",
        "B07i-design-range-pair",
        "B07j-ratio-positive",
    ):
        expected = _expected(case_id)
        assert expected["status"] == "error"
        assert expected["error_type"] == "ValidationError"
        assert expected["message"]

    near_null_request = json.loads((GOLDEN_ROOT / "requests" / "B07b-near-null.json").read_text())
    assert near_null_request["design_true_effects"] == [1.2e-12]
    near_null = _response("B07b-near-null")
    scenario = next(
        row for row in near_null["design"]["scenarios"] if row["source"] == "custom_true_effect"
    )
    assert scenario["type_s"] is None
    assert scenario["type_m"] is None
    assert scenario["observed_exaggeration"] is None

    disabled_design = _response("B07k-disabled-design-ignored")
    assert disabled_design["design"] is None
    assert compare_values(_response("B01"), disabled_design) == []


def test_b08_extreme_summaries_remain_finite_and_warn_when_clipped() -> None:
    for case_id in (
        "B08a-additive-midpoint",
        "B08b-s-minus-2-clipping",
        "B08c-log-likelihood-fallback",
        "B08d-ratio-natural-clipping",
    ):
        response = _response(case_id)
        assert all(field["all_numeric_values_finite"] for field in response["grid"].values())

    midpoint = _response("B08a-additive-midpoint")
    assert midpoint["summary"]["estimate_working"] == 0.0

    s_minus_2 = _response("B08b-s-minus-2-clipping")
    assert s_minus_2["meta"]["s_minus_2_interval"]["range_working"][1] == sys.float_info.max
    assert any("S-2 interval endpoints were clipped" in item for item in s_minus_2["warnings"])

    likelihood = _response("B08c-log-likelihood-fallback")
    assert likelihood["summary"]["likelihood_ratio_mle_to_null"] is None
    assert likelihood["summary"]["log_likelihood_ratio_mle_to_null"] is not None

    ratio = _response("B08d-ratio-natural-clipping")
    assert ratio["grid"]["effect_display"]["last"] == sys.float_info.max
    assert any("Natural-axis x-values were clipped" in item for item in ratio["warnings"])

    rejected = _expected("B08e-unrepresentable-design-distance")
    assert rejected["status"] == "error"
    assert rejected["error_type"] == "ValidationError"
    assert rejected["message"] == (
        "Design standardized distance exceeds the finite floating-point range."
    )


def test_export_schema_fixtures_match_browser_sources() -> None:
    schemas = json.loads((GOLDEN_ROOT / "export_schemas" / "csv_columns.json").read_text())
    renderer = (PROJECT_ROOT / "web" / "assets" / "renderers.js").read_text()
    csv_source = renderer[
        renderer.index("export function buildCsv") : renderer.index(
            "export function renderDesignResults"
        )
    ]
    position = -1
    for column in schemas["design_enabled"]:
        position = csv_source.index(f'"{column}"', position + 1)

    figures = json.loads((GOLDEN_ROOT / "export_schemas" / "figure_exports.json").read_text())
    plot_source = (PROJECT_ROOT / "web" / "assets" / "plot.js").read_text()
    assert 'height = plotElement.dataset.designEnabled === "true" ? 1600 : 1100' in plot_source
    assert "const exportHeight = hasDesign(response) ? 1500 : 1000" in plot_source
    assert f"width: {figures['dashboard']['width']}" in plot_source
    assert f"scale: {figures['dashboard']['scale']}" in plot_source

    index_source = (PROJECT_ROOT / "web" / "index.html").read_text()
    for control_id in figures["controls"]:
        assert f'id="{control_id}"' in index_source
