from __future__ import annotations

from pathlib import Path

import pytest
from helpers import wait_for_ready
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def enable_design(page: Page) -> None:
    page.locator("#design-enabled").check()
    wait_for_ready(page)
    expect(page.locator("#design-results")).to_be_visible()


def test_design_controls_are_default_off_and_enable_results(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    expect(page.locator("#design-enabled")).not_to_be_checked()
    expect(page.locator("#design-fields")).to_be_hidden()
    expect(page.locator("#design-alpha")).to_be_disabled()
    expect(page.locator("#design-selection-rule")).to_be_disabled()
    expect(page.locator("#design-results")).to_be_hidden()

    enable_design(page)
    expect(page.locator("#design-fields")).to_be_visible()
    expect(page.locator("#design-alpha")).to_be_enabled()
    expect(page.locator("#design-selection-rule")).to_be_enabled()
    expect(page.locator("#summary-grid")).to_contain_text("Design calibration")
    expect(page.locator("#design-summary")).to_contain_text("alpha = 0.05")
    expect(page.locator("#design-summary")).to_contain_text("information = 1x")
    expect(page.locator("#design-scenario-table")).to_contain_text("CI-implied estimate")
    expect(page.locator("#reviewer-text")).to_contain_text(
        "not posterior probabilities that the observed result is wrong"
    )
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          return plot?.data?.length === 3
            && plot.data.some((trace) => trace.name === "Power");
        }
        """,
        timeout=120000,
    )

    page.locator("#design-enabled").uncheck()
    wait_for_ready(page)
    expect(page.locator("#design-results")).to_be_hidden()
    page.wait_for_function(
        """
        () => document.getElementById("curve-plot")?.data?.length === 2
        """,
        timeout=120000,
    )


def test_design_metric_selector_changes_design_trace(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)

    page.select_option("#design-metric", "type_m")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          const titles = Array.from(plot?.querySelectorAll(".g-y3title text") ?? [])
            .map((node) => node.textContent?.trim());
          return plot?.data?.some((trace) => trace.name === "Type M exaggeration")
            && titles.includes("Type M exaggeration ratio");
        }
        """,
        timeout=120000,
    )
    expect(page.locator("#warnings-list")).to_contain_text("Type M is computed on the log")


def test_design_likelihood_only_panel_labels_are_unique(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)

    page.locator("#view-mode-likelihood").check()
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          const annotations = plot?._fullLayout?.annotations?.map((item) => item.text) ?? [];
          const likelihoodLabel =
            "B. Relative likelihood (normalized to 1 at the CI-implied estimate)";
          const designLabel =
            "C. Design calibration (assumed true-effect operating characteristics)";
          return plot?.dataset?.viewMode === "likelihood"
            && annotations.includes(likelihoodLabel)
            && annotations.includes(designLabel);
        }
        """,
        timeout=120000,
    )


def test_invalid_design_inputs_surface_errors(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.locator("#design-enabled").check()
    page.locator("#design-alpha").fill("1")
    page.locator("#design-alpha").blur()
    expect(page.locator("#status-card")).to_contain_text(
        "Selection threshold alpha must be greater than 0 and less than 1",
        timeout=120000,
    )
    expect(page.locator("#curve-plot .main-svg")).to_have_count(0)

    page.locator("#design-alpha").fill("0.05")
    page.locator("#design-true-effects").fill("-1")
    page.locator("#design-true-effects").blur()
    expect(page.locator("#status-card")).to_contain_text("strictly positive", timeout=120000)


def test_design_selection_rule_and_threshold_controls_update_summary(
    app_url: str, page: Page
) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)

    page.select_option("#design-selection-rule", "ci_excludes_mcid")
    expect(page.locator("#design-claim-direction-group")).to_be_visible()
    expect(page.locator("#design-claim-threshold-group")).to_be_visible()
    page.locator("#design-claim-threshold").fill("1.25")
    wait_for_ready(page)

    expect(page.locator("#design-summary")).to_contain_text(
        "CI at selected alpha excludes the claim threshold"
    )
    expect(page.locator("#summary-grid")).to_contain_text(
        "CI at selected alpha excludes the claim threshold"
    )
    expect(page.locator("#warnings-list")).to_contain_text(
        "Selected-claim rule: CI at selected alpha excludes the claim threshold"
    )


def test_threshold_rule_requires_threshold(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)

    page.select_option("#design-selection-rule", "ci_excludes_mcid")
    expect(page.locator("#status-card")).to_contain_text(
        "requires a finite claim threshold", timeout=120000
    )
    expect(page.locator("#curve-plot .main-svg")).to_have_count(0)


def test_information_multiplier_changes_design_not_observed_traces(
    app_url: str, page: Page
) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)

    before = page.locator("#curve-plot").evaluate(
        """
        (plot) => ({
          compatibility: plot.data[0].y.slice(0, 12),
          likelihood: plot.data[1].y.slice(0, 12),
          design: plot.data[plot.data.length - 1].y.slice(0, 12),
        })
        """
    )
    page.locator("#design-information-multiplier").fill("4")
    expect(page.locator("#design-summary")).to_contain_text("information = 4x", timeout=120000)
    after = page.locator("#curve-plot").evaluate(
        """
        (plot) => ({
          compatibility: plot.data[0].y.slice(0, 12),
          likelihood: plot.data[1].y.slice(0, 12),
          design: plot.data[plot.data.length - 1].y.slice(0, 12),
        })
        """
    )

    assert after["compatibility"] == before["compatibility"]
    assert after["likelihood"] == before["likelihood"]
    assert after["design"] != before["design"]
    expect(page.locator("#design-summary")).to_contain_text("information = 4x")


def test_precision_target_table_and_reviewer_text_render(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)

    page.locator("#design-true-effects").fill("1.25")
    page.select_option("#design-precision-target-effect", "1.25")
    page.locator("#design-max-type-m").fill("1.25")
    wait_for_ready(page)

    expect(page.locator("#design-precision-target-table")).to_contain_text("Power")
    expect(page.locator("#design-precision-target-table")).to_contain_text("Information multiplier")
    expect(page.locator("#reviewer-text")).to_contain_text("precision target")


def test_design_csv_and_png_exports_include_design_panel(
    app_url: str, page: Page, tmp_path: Path
) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)
    page.locator("#design-true-effects").fill("1.25")
    wait_for_ready(page)

    with page.expect_download() as csv_download_info:
        page.locator("#export-csv").click()
    csv_download = csv_download_info.value
    csv_path = tmp_path / csv_download.suggested_filename
    csv_download.save_as(csv_path)
    assert "design_power_if_true" in csv_path.read_text(encoding="utf-8").splitlines()[0]

    with page.expect_download() as png_download_info:
        page.locator("#export-png").click()
    png_download = png_download_info.value
    png_path = tmp_path / png_download.suggested_filename
    png_download.save_as(png_path)
    assert png_path.stat().st_size > 0
