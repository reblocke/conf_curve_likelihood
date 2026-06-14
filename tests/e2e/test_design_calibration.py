from __future__ import annotations

from pathlib import Path

import pytest
from helpers import plot_annotation_texts, wait_for_ready, x_axis_titles
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

DESIGN_PANEL_LABELS = [
    "C. Design calibration: selected-claim probability if x is true",
    "D. Design calibration: Type S probability if x is true",
    "E. Design calibration: Type M exaggeration if x is true",
    "F. Design calibration: observed exaggeration if x is true",
]


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
          const annotations = plot?._fullLayout?.annotations?.map((item) => item.text) ?? [];
          const traceNames = plot?.data?.map((trace) => trace.name) ?? [];
          return plot?.data?.length === 6
            && plot.data.some((trace) => trace.name === "Power")
            && traceNames.includes("Type S probability")
            && traceNames.includes("Type M exaggeration")
            && traceNames.includes("Observed exaggeration if true")
            && [
              "C. Design calibration: selected-claim probability if x is true",
              "D. Design calibration: Type S probability if x is true",
              "E. Design calibration: Type M exaggeration if x is true",
              "F. Design calibration: observed exaggeration if x is true",
            ].every((label) => annotations.includes(label));
        }
        """,
        timeout=120000,
    )
    expect(page.locator("#design-metric")).to_have_count(0)
    expect(page.locator("#design-results")).not_to_contain_text("Changes panel C only")
    assert "Design threshold" not in plot_annotation_texts(page)
    assert x_axis_titles(page) == [
        "Odds ratio (natural scale; design panels treat x as the assumed true effect)"
    ]

    page.locator("#design-enabled").uncheck()
    wait_for_ready(page)
    expect(page.locator("#design-results")).to_be_hidden()
    page.wait_for_function(
        """
        () => document.getElementById("curve-plot")?.data?.length === 2
        """,
        timeout=120000,
    )


def test_design_panels_show_all_metrics_and_cap_ratio_curves(app_url: str, page: Page) -> None:
    page.set_viewport_size({"width": 1440, "height": 1100})
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)
    page.locator("#design-true-effects").fill("1.01")
    wait_for_ready(page)

    panel_state = page.locator("#curve-plot").evaluate(
        """
        (plot) => {
          const byName = Object.fromEntries(plot.data.map((trace) => [trace.name, trace]));
          const typeM = byName["Type M exaggeration"];
          const observed = byName["Observed exaggeration if true"];
          const firstOmittedTypeM = typeM.y.findIndex((value, index) =>
            value === null && Number.parseFloat(typeM.customdata[index][4]) > 10
          );
          const firstOmittedObserved = observed.y.findIndex((value, index) =>
            value === null && Number.parseFloat(observed.customdata[index][5]) > 10
          );
          const yTitleSelectors = [
            ".g-ytitle text",
            ".g-y2title text",
            ".g-y3title text",
            ".g-y4title text",
            ".g-y5title text",
            ".g-y6title text",
          ].join(", ");
          return {
            names: plot.data.map((trace) => trace.name),
            yAxisTitles: Array.from(
              plot.querySelectorAll(yTitleSelectors) ?? []
            ).map((node) => node.textContent?.trim()).filter(Boolean),
            typeMUpper: plot._fullLayout.yaxis5.range[1],
            observedUpper: plot._fullLayout.yaxis6.range[1],
            typeMTickText: plot._fullLayout.yaxis5.ticktext,
            observedTickText: plot._fullLayout.yaxis6.ticktext,
            twoXGuideCount: plot._fullLayout.shapes.filter((shape) =>
              shape.type === "line"
              && ["y5", "y6"].includes(shape.yref)
              && Math.abs(shape.y0 - 2) < 1e-9
              && Math.abs(shape.y1 - 2) < 1e-9
            ).length,
            firstOmittedTypeM,
            firstOmittedObserved,
          };
        }
        """
    )
    assert panel_state["names"] == [
        "Compatibility / confidence curve",
        "Relative likelihood curve",
        "Power",
        "Type S probability",
        "Type M exaggeration",
        "Observed exaggeration if true",
    ]
    assert "Type M (x-fold exaggeration)" in panel_state["yAxisTitles"]
    assert "Observed ratio (x-fold)" in panel_state["yAxisTitles"]
    assert panel_state["typeMUpper"] <= 10
    assert panel_state["observedUpper"] <= 10
    assert panel_state["typeMTickText"] == ["0", "1x", "2x", "5x", "10x"]
    assert panel_state["observedTickText"] == ["0", "1x", "2x", "5x", "10x"]
    assert panel_state["twoXGuideCount"] == 2
    assert panel_state["firstOmittedTypeM"] >= 0
    assert panel_state["firstOmittedObserved"] >= 0

    custom_row = page.locator("#design-scenario-table tbody tr").filter(has_text="1.01")
    type_m_text = custom_row.locator("td").nth(5).inner_text().replace("x", "")
    assert float(type_m_text) > 10
    expect(page.locator("#warnings-list")).to_contain_text(
        "1x means no exaggeration and 2x means a two-fold magnitude overestimate"
    )
    expect(page.locator("#warnings-list")).to_contain_text("values above 10x are omitted")
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
            "B. Observed likelihood: candidate effects compared with the CI-implied estimate";
          const designLabel =
            "C. Design calibration: selected-claim probability if x is true";
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
    expect(page.locator("#plot-key")).to_contain_text("Claim threshold for selected-claim rule")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          const annotations = plot?._fullLayout?.annotations?.map((item) => item.text) ?? [];
          const claimThresholdShape = plot?._fullLayout?.shapes?.some((shape) =>
            shape.xref === "x3"
              && shape.yref === "paper"
              && shape.y0 < 0.2
              && shape.y1 > 0.6
              && Math.abs(shape.x0 - 1.25) < 1e-9
          );
          return annotations.includes("Claim threshold 1.25")
            && !annotations.some((text) => String(text).includes("Design threshold"))
            && claimThresholdShape;
        }
        """,
        timeout=120000,
    )


def test_design_panel_labels_do_not_overlap_desktop(app_url: str, page: Page) -> None:
    page.set_viewport_size({"width": 1440, "height": 1100})
    page.goto(app_url)
    wait_for_ready(page)
    enable_design(page)

    overlaps = page.locator("#curve-plot").evaluate(
        """
        (plot) => {
          const importantLabels = new Set([
            "A. Observed compatibility: candidate effects compared with the reported CI",
            "B. Observed likelihood: candidate effects compared with the CI-implied estimate",
            "C. Design calibration: selected-claim probability if x is true",
            "D. Design calibration: Type S probability if x is true",
            "E. Design calibration: Type M exaggeration if x is true",
            "F. Design calibration: observed exaggeration if x is true",
            "Estimate",
            "Null",
          ]);
          const nodes = Array.from(plot.querySelectorAll(".annotation-text"))
            .filter((node) => importantLabels.has(node.textContent?.trim()));
          const boxes = nodes.map((node) => ({
            text: node.textContent?.trim(),
            box: node.getBoundingClientRect(),
          }));
          const overlaps = [];
          for (let i = 0; i < boxes.length; i += 1) {
            for (let j = i + 1; j < boxes.length; j += 1) {
              const a = boxes[i].box;
              const b = boxes[j].box;
              const separated = a.right <= b.left
                || a.left >= b.right
                || a.bottom <= b.top
                || a.top >= b.bottom;
              if (!separated) {
                overlaps.push(`${boxes[i].text} / ${boxes[j].text}`);
              }
            }
          }
          return overlaps;
        }
        """
    )
    assert overlaps == []

    ratio_title_overlap = page.locator("#curve-plot").evaluate(
        """
        (plot) => {
          const typeMTitle = plot.querySelector(".g-y5title text");
          const observedTitle = plot.querySelector(".g-y6title text");
          if (!typeMTitle || !observedTitle) {
            return true;
          }
          const a = typeMTitle.getBoundingClientRect();
          const b = observedTitle.getBoundingClientRect();
          return !(
            a.right <= b.left
            || a.left >= b.right
            || a.bottom <= b.top
            || a.top >= b.bottom
          );
        }
        """
    )
    assert ratio_title_overlap is False


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
          design: plot.data.find((trace) => trace.name === "Power").y.slice(0, 12),
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
          design: plot.data.find((trace) => trace.name === "Power").y.slice(0, 12),
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
    expect(page.locator("#figure-caption")).to_contain_text("design-calibration panels")

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
