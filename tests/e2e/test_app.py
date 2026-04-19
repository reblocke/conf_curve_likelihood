from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def wait_for_ready(page: Page) -> None:
    expect(page.locator("#status-card")).to_contain_text("Curves updated", timeout=120000)


def paper_shape_x_values(page: Page) -> list[float]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => element._fullLayout.shapes
          .filter((shape) => shape.yref === "paper")
          .map((shape) => shape.x0)
          .sort((left, right) => left - right)
        """
    )


def xaxis_type(page: Page) -> str:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => element._fullLayout.xaxis.type || "linear"
        """
    )


def xaxis_tick_labels(page: Page) -> list[str]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => (element._fullLayout.xaxis.ticktext || []).map((label) => String(label))
        """
    )


def plot_trace_names(page: Page) -> list[str]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => element.data.map((trace) => trace.name)
        """
    )


def y_axis_titles(page: Page) -> list[str]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => Array.from(element.querySelectorAll(".g-ytitle text, .g-y2title text"))
          .map((node) => node.textContent?.trim())
          .filter(Boolean)
        """
    )


def plot_annotation_texts(page: Page) -> list[str]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => (element._fullLayout.annotations || [])
          .map((annotation) => String(annotation.text))
        """
    )


def open_advanced_options(page: Page) -> None:
    page.locator("#advanced-display-options").evaluate("(element) => { element.open = true; }")
    expect(page.locator("#advanced-display-options")).to_have_attribute("open", "")


def xaxis_upper_bound(page: Page) -> float:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => {
          const axis = element._fullLayout.xaxis;
          return axis.type === "log" ? 10 ** axis.range[1] : axis.range[1];
        }
        """
    )


def xaxis_bounds(page: Page) -> list[float]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => {
          const axis = element._fullLayout.xaxis;
          return axis.type === "log"
            ? [10 ** axis.range[0], 10 ** axis.range[1]]
            : [axis.range[0], axis.range[1]];
        }
        """
    )


def xaxis_pixel_positions(page: Page, values: list[float]) -> list[float]:
    return page.locator("#curve-plot").evaluate(
        """
        (element, requestedValues) =>
          requestedValues.map((value) => element._fullLayout.xaxis.d2p(value))
        """,
        values,
    )


def horizontal_cutoff_count(page: Page) -> int:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => element._fullLayout.shapes
          .filter((shape) => shape.yref === "y")
          .length
        """
    )


def plot_width_metrics(page: Page) -> dict[str, float]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => {
          const surface = element.getBoundingClientRect();
          const svg = element.querySelector(".main-svg")?.getBoundingClientRect();
          return {
            surface: surface.width,
            svg: svg?.width ?? 0,
            layout: element._fullLayout?.width ?? 0,
          };
        }
        """
    )


def test_initial_render_loads_pyodide_and_plots(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    expect(page.locator("label[for='estimate']")).to_have_text("Point Estimate (optional)")
    expect(page.locator("#plot-title")).to_contain_text(
        "How the data compare candidate odds ratios"
    )
    expect(page.locator("#plot-subtitle")).to_contain_text(
        "Relative to the null and the CI-implied estimate"
    )
    expect(page.locator("#comparison-takeaway")).to_contain_text("Peak support is at OR")
    expect(page.locator("#read-guide")).to_contain_text("two-sided Wald p-value function")
    expect(page.locator("#read-guide")).to_contain_text(
        "does not reconstruct the exact fitted-model profile likelihood"
    )
    expect(page.locator("#summary-grid")).to_contain_text("Estimate source")
    expect(page.locator("#summary-grid")).to_contain_text("Main comparison")
    expect(page.locator("#summary-grid")).to_contain_text("Technical reconstruction")
    expect(page.locator("#plot-key")).to_contain_text("Point estimate")
    expect(page.locator("#plot-key")).to_contain_text("Null value")
    expect(page.locator("#plot-key")).to_contain_text("Design threshold markers")
    expect(page.locator("#plot-key")).to_contain_text("Compatibility cutoffs")
    expect(page.locator("#plot-key")).not_to_contain_text("Clinical thresholds")
    expect(page.locator("#commentary-text")).to_contain_text("CI-implied midpoint")
    expect(page.locator("#figure-caption")).to_contain_text("Wald reconstruction")
    expect(page.locator("#figure-caption")).to_contain_text(
        "not exact fitted-model profile likelihood"
    )
    expect(page.locator("#curve-plot .main-svg").first).to_be_visible()


def test_comparison_header_updates_for_thresholds_and_effect_measure(
    app_url: str, page: Page
) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.locator("#thresholds").fill("1.25")
    page.wait_for_function(
        """
        () => document.getElementById("plot-subtitle")
          ?.textContent?.includes("clinical thresholds")
        """,
        timeout=120000,
    )
    expect(page.locator("#plot-subtitle")).to_contain_text(
        "Relative to the null OR = 1 and clinical thresholds"
    )
    expect(page.locator("#comparison-takeaway")).to_contain_text("clinical threshold OR = 1.25")

    page.select_option("#effect-type", "mean_difference")
    page.locator("#ci-lower").fill("0.11")
    page.locator("#ci-upper").fill("0.73")
    page.locator("#thresholds").fill("0.5")
    page.wait_for_function(
        """
        () => document.getElementById("plot-title")
          ?.textContent?.includes("candidate mean differences")
        """,
        timeout=120000,
    )

    expect(page.locator("#plot-title")).to_contain_text("candidate mean differences")
    expect(page.locator("#plot-subtitle")).to_contain_text(
        "Relative to the null mean difference = 0 and clinical thresholds"
    )


def test_advanced_display_options_hide_and_show_moved_controls(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    expect(page.locator("#advanced-display-options")).not_to_have_attribute("open", "")
    expect(page.locator("#axis-spacing-group")).to_be_hidden()

    open_advanced_options(page)

    expect(page.locator("#axis-spacing-group")).to_be_visible()
    expect(page.locator("#display-range-group")).to_be_visible()
    expect(page.locator("#grid-points")).to_be_visible()
    expect(page.locator("#show-cutoffs")).to_be_visible()

    page.locator("#show-cutoffs").uncheck()
    wait_for_ready(page)
    expect(page.locator("#status-card")).to_contain_text("Curves updated")


def test_direct_labels_and_panel_annotations_render_on_plot(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    annotations = plot_annotation_texts(page)
    assert "Estimate" in annotations
    assert "Null" in annotations
    assert "Design threshold" in annotations
    assert "A. Compatibility curve (two-sided Wald p-value function)" in annotations
    assert "B. Relative likelihood (normalized to 1 at the CI-implied estimate)" in annotations
    _, default_upper_bound = xaxis_bounds(page)
    assert default_upper_bound < 10

    page.locator("#thresholds").fill("1.25")
    page.wait_for_function(
        """
        () => (document.getElementById("curve-plot")?._fullLayout?.annotations || [])
          .some((annotation) => String(annotation.text).includes("Threshold 1.25"))
        """,
        timeout=120000,
    )
    assert "Threshold 1.25" in plot_annotation_texts(page)


def test_summary_puts_main_comparison_before_technical_reconstruction(
    app_url: str, page: Page
) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    headings = page.locator("#summary-grid .summary-group-title").all_text_contents()
    assert headings[:2] == ["Main comparison", "Technical reconstruction"]
    expect(page.locator("#summary-grid")).to_contain_text("Point Estimate")
    expect(page.locator("#summary-grid")).to_contain_text("95% CI")
    expect(page.locator("#summary-grid")).to_contain_text("Working-scale SE")


def test_effect_type_switch_updates_controls(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.select_option("#effect-type", "mean_difference")
    page.locator("#ci-lower").fill("0.11")
    page.locator("#ci-upper").fill("0.73")
    page.wait_for_function(
        """
        () => document.getElementById("curve-plot")?._fullLayout?.xaxis?.type === "linear"
        """,
        timeout=120000,
    )
    open_advanced_options(page)

    expect(page.locator("#axis-spacing-group")).to_be_hidden()
    expect(page.locator("#null-value")).to_have_value("0")
    assert xaxis_type(page) == "linear"


def test_ratio_default_view_uses_natural_labels_with_logarithmic_spacing(
    app_url: str, page: Page
) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    expect(page.locator("#axis-spacing-group")).to_be_visible()
    expect(page.locator("#axis-spacing")).to_have_value("log")
    assert xaxis_type(page) == "log"
    assert any(label.startswith("0.") for label in xaxis_tick_labels(page))


def test_ratio_spacing_toggle_changes_axis_type_but_keeps_the_same_point_estimate(
    app_url: str, page: Page
) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    log_positions = xaxis_pixel_positions(page, [1.0, 1.8])
    page.select_option("#axis-spacing", "linear")
    page.wait_for_function(
        """
        () => document.getElementById("curve-plot")?._fullLayout?.xaxis?.type === "linear"
        """,
        timeout=120000,
    )

    expect(page.locator("#summary-grid")).to_contain_text("Point Estimate")
    expect(page.locator("#summary-grid")).to_contain_text("1.8")
    assert xaxis_type(page) == "linear"

    linear_positions = xaxis_pixel_positions(page, [1.0, 1.8])
    assert (linear_positions[1] - linear_positions[0]) != pytest.approx(
        log_positions[1] - log_positions[0]
    )


def test_blank_estimate_still_computes_successfully(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    expect(page.locator("#estimate")).to_have_value("")
    expect(page.locator("#summary-grid")).to_contain_text("CI-implied from 95% CI")


def test_effect_type_switch_preserves_custom_null_but_updates_defaults(
    app_url: str, page: Page
) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.select_option("#effect-type", "mean_difference")
    page.locator("#ci-lower").fill("0.11")
    page.locator("#ci-upper").fill("0.73")
    wait_for_ready(page)
    expect(page.locator("#null-value")).to_have_value("0")

    page.locator("#null-value").fill("1.5")
    page.select_option("#effect-type", "odds_ratio")
    page.locator("#ci-lower").fill("1.2")
    page.locator("#ci-upper").fill("2.7")
    wait_for_ready(page)
    expect(page.locator("#null-value")).to_have_value("1.5")


def test_estimate_mismatch_surfaces_validation_error(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.select_option("#effect-type", "mean_difference")
    page.locator("#estimate").fill("0.5")
    page.locator("#ci-lower").fill("0.11")
    page.locator("#ci-upper").fill("0.73")
    page.locator("#estimate").blur()

    expect(page.locator("#status-card")).to_contain_text(
        "inconsistent with the supplied 95% confidence interval", timeout=120000
    )
    expect(page.locator("#export-csv")).to_be_disabled()
    expect(page.locator("#export-png")).to_be_disabled()
    expect(page.locator("#summary-grid")).to_be_empty()
    expect(page.locator("#curve-plot .main-svg")).to_have_count(0)


def test_invalid_ratio_input_surfaces_validation_error(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.locator("#ci-lower").fill("0")
    page.locator("#ci-lower").blur()

    expect(page.locator("#status-card")).to_contain_text("strictly positive", timeout=120000)
    expect(page.locator("#export-csv")).to_be_disabled()
    expect(page.locator("#export-png")).to_be_disabled()
    expect(page.locator("#summary-grid")).to_be_empty()
    expect(page.locator("#curve-plot .main-svg")).to_have_count(0)


def test_threshold_input_adds_plot_markers(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    assert len(paper_shape_x_values(page)) == 4
    page.locator("#thresholds").fill("0.8, 1.25")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          return plot?._fullLayout?.shapes?.filter((shape) => shape.yref === "paper").length === 6;
        }
        """,
        timeout=120000,
    )

    assert len(paper_shape_x_values(page)) == 6


def test_threshold_and_grid_point_controls_are_visibly_separated(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    thresholds_section_text = page.locator("#thresholds").evaluate(
        "(input) => input.closest('section').textContent"
    )
    grid_points_section_text = page.locator("#grid-points").evaluate(
        "(input) => input.closest('section').textContent"
    )

    assert "Grid points" not in thresholds_section_text
    assert "Clinical thresholds" not in grid_points_section_text

    page.locator("#grid-points").evaluate(
        """
        (input, value) => {
          input.value = value;
          input.dispatchEvent(new Event("input", { bubbles: true }));
        }
        """,
        "1001",
    )
    assert page.locator("#grid-points-output").text_content() == "1001"
    assert page.locator("#thresholds").input_value() == ""


def test_cutoff_checkbox_toggles_horizontal_guides(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    assert horizontal_cutoff_count(page) == 3
    page.locator("#show-cutoffs").uncheck()
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          return plot?._fullLayout?.shapes?.filter((shape) => shape.yref === "y").length === 0;
        }
        """,
        timeout=120000,
    )
    assert horizontal_cutoff_count(page) == 0

    page.locator("#show-cutoffs").check()
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          return plot?._fullLayout?.shapes?.filter((shape) => shape.yref === "y").length === 3;
        }
        """,
        timeout=120000,
    )
    assert horizontal_cutoff_count(page) == 3


def test_plot_key_tracks_thresholds_and_cutoffs(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    expect(page.locator("#plot-key")).not_to_contain_text("Clinical thresholds")
    expect(page.locator("#plot-key")).to_contain_text("Compatibility cutoffs")

    page.locator("#thresholds").fill("0.8, 1.25")
    page.wait_for_function(
        """
        () => document.getElementById("plot-key")?.textContent?.includes("Clinical thresholds")
        """,
        timeout=120000,
    )
    expect(page.locator("#plot-key")).to_contain_text("Clinical thresholds")

    page.locator("#show-cutoffs").uncheck()
    page.wait_for_function(
        """
        () => !document.getElementById("plot-key")?.textContent?.includes("Compatibility cutoffs")
        """,
        timeout=120000,
    )
    expect(page.locator("#plot-key")).not_to_contain_text("Compatibility cutoffs")


def test_critical_effect_markers_are_visible_on_plot(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    x_values = paper_shape_x_values(page)
    assert len(x_values) == 4
    assert x_values[0] < 1.0
    assert x_values[-1] > 1.0


def test_distant_markers_expand_the_x_axis_extent(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.locator("#null-value").fill("12")
    page.locator("#thresholds").fill("8")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          if (!plot?._fullLayout?.xaxis?.range) {
            return false;
          }
          const axis = plot._fullLayout.xaxis;
          const upperBound = axis.type === "log" ? 10 ** axis.range[1] : axis.range[1];
          return upperBound > 12;
        }
        """,
        timeout=120000,
    )

    assert xaxis_upper_bound(page) > 12


def test_ratio_plausible_display_range_constrains_plot_and_warns(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    page.locator("#display-range-lower").fill("0.9")
    page.locator("#display-range-upper").fill("1.1")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          if (!plot?._fullLayout?.xaxis?.range) {
            return false;
          }
          const axis = plot._fullLayout.xaxis;
          const bounds = axis.type === "log"
            ? [10 ** axis.range[0], 10 ** axis.range[1]]
            : [axis.range[0], axis.range[1]];
          return Math.abs(bounds[0] - 0.9) < 1e-6 && Math.abs(bounds[1] - 1.1) < 1e-6;
        }
        """,
        timeout=120000,
    )

    lower_bound, upper_bound = xaxis_bounds(page)
    assert lower_bound == pytest.approx(0.9)
    assert upper_bound == pytest.approx(1.1)
    expect(page.locator("#warnings-list")).to_contain_text(
        "The chosen display range excludes the point estimate."
    )
    expect(page.locator("#warnings-list")).to_contain_text(
        "The chosen display range excludes the lower 95% CI bound."
    )
    expect(page.locator("#warnings-list")).to_contain_text(
        "The chosen display range excludes one or more critical-effect markers."
    )


def test_plausible_display_range_csv_exports_current_grid(
    app_url: str, page: Page, tmp_path: Path
) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    page.locator("#display-range-lower").fill("0.9")
    page.locator("#display-range-upper").fill("1.1")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          if (!plot?._fullLayout?.xaxis?.range) {
            return false;
          }
          const axis = plot._fullLayout.xaxis;
          const upperBound = axis.type === "log" ? 10 ** axis.range[1] : axis.range[1];
          return Math.abs(upperBound - 1.1) < 1e-6;
        }
        """,
        timeout=120000,
    )

    with page.expect_download() as download_info:
        page.locator("#export-csv").click()
    download = download_info.value

    csv_path = tmp_path / download.suggested_filename
    download.save_as(csv_path)
    rows = csv_path.read_text(encoding="utf-8").strip().splitlines()
    first_effect = float(rows[1].split(",")[0])
    last_effect = float(rows[-1].split(",")[0])
    assert first_effect == pytest.approx(0.9)
    assert last_effect == pytest.approx(1.1)


def test_invalid_plausible_display_range_clears_rendered_state(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    page.locator("#display-range-lower").fill("1.2")
    page.locator("#display-range-upper").fill("1.1")
    page.locator("#display-range-upper").blur()

    expect(page.locator("#status-card")).to_contain_text(
        "Plausible display range lower must be less", timeout=120000
    )
    expect(page.locator("#export-csv")).to_be_disabled()
    expect(page.locator("#export-png")).to_be_disabled()
    expect(page.locator("#export-manuscript-png")).to_be_disabled()
    expect(page.locator("#summary-grid")).to_be_empty()
    expect(page.locator("#curve-plot .main-svg")).to_have_count(0)


def test_clearing_plausible_display_range_restores_auto_behavior(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)
    open_advanced_options(page)

    page.locator("#display-range-lower").fill("0.9")
    page.locator("#display-range-upper").fill("1.1")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          if (!plot?._fullLayout?.xaxis?.range) {
            return false;
          }
          const axis = plot._fullLayout.xaxis;
          const upperBound = axis.type === "log" ? 10 ** axis.range[1] : axis.range[1];
          return Math.abs(upperBound - 1.1) < 1e-6;
        }
        """,
        timeout=120000,
    )

    page.locator("#display-range-lower").fill("")
    page.locator("#display-range-upper").fill("")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          if (!plot?._fullLayout?.xaxis?.range) {
            return false;
          }
          const axis = plot._fullLayout.xaxis;
          const bounds = axis.type === "log"
            ? [10 ** axis.range[0], 10 ** axis.range[1]]
            : [axis.range[0], axis.range[1]];
          return bounds[0] < 0.9 && bounds[1] > 2.7;
        }
        """,
        timeout=120000,
    )

    lower_bound, upper_bound = xaxis_bounds(page)
    assert lower_bound < 0.9
    assert upper_bound > 2.7


def test_likelihood_only_view_hides_compatibility_panel(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.locator("#view-mode-likelihood").check()
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          return plot?.dataset?.viewMode === "likelihood" && plot.data?.length === 1;
        }
        """,
        timeout=120000,
    )

    assert plot_trace_names(page) == ["Relative likelihood curve"]
    assert y_axis_titles(page) == ["Relative likelihood"]
    assert horizontal_cutoff_count(page) == 0
    expect(page.locator("#plot-key")).not_to_contain_text("Compatibility cutoffs")
    expect(page.locator("#commentary-text")).to_contain_text("relative evidentiary support")


def test_compatibility_only_view_hides_likelihood_panel(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.locator("#view-mode-compatibility").check()
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          return plot?.dataset?.viewMode === "compatibility" && plot.data?.length === 1;
        }
        """,
        timeout=120000,
    )

    assert plot_trace_names(page) == ["Compatibility / confidence curve"]
    assert y_axis_titles(page) == ["Compatibility / confidence curve"]
    assert horizontal_cutoff_count(page) == 3
    expect(page.locator("#plot-key")).to_contain_text("Compatibility cutoffs")
    expect(page.locator("#commentary-text")).to_contain_text("two-sided Wald p-value function")


def test_y_axis_titles_are_visible(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          const titles = Array.from(
            plot?.querySelectorAll(".g-ytitle text, .g-y2title text") ?? []
          )
            .map((node) => node.textContent?.trim())
            .filter(Boolean);
          return titles.includes("Compatibility / confidence curve")
            && titles.includes("Relative likelihood");
        }
        """,
        timeout=120000,
    )

    titles = y_axis_titles(page)
    assert "Compatibility / confidence curve" in titles
    assert "Relative likelihood" in titles


def test_csv_export_downloads_current_grid(app_url: str, page: Page, tmp_path: Path) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    with page.expect_download() as download_info:
        page.locator("#export-csv").click()
    download = download_info.value

    csv_path = tmp_path / download.suggested_filename
    download.save_as(csv_path)
    assert csv_path.read_text(encoding="utf-8").startswith(
        "effect_display,effect_working,z,compatibility,relative_likelihood,log_relative_likelihood"
    )


def test_png_export_downloads_combined_figure(app_url: str, page: Page, tmp_path: Path) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    with page.expect_download() as download_info:
        page.locator("#export-png").click()
    download = download_info.value

    png_path = tmp_path / download.suggested_filename
    download.save_as(png_path)
    assert png_path.stat().st_size > 0


def test_png_export_works_in_single_panel_view_modes(
    app_url: str, page: Page, tmp_path: Path
) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    for mode in ("likelihood", "compatibility"):
        page.locator(f"#view-mode-{mode}").check()
        page.wait_for_function(
            """
            (expectedMode) => {
              const plot = document.getElementById("curve-plot");
              return plot?.dataset?.viewMode === expectedMode && plot.data?.length === 1;
            }
            """,
            arg=mode,
            timeout=120000,
        )

        with page.expect_download() as download_info:
            page.locator("#export-png").click()
        download = download_info.value

        png_path = tmp_path / f"{mode}-{download.suggested_filename}"
        download.save_as(png_path)
        assert png_path.stat().st_size > 0


def test_manuscript_png_export_works_without_embedding_caption(
    app_url: str, page: Page, tmp_path: Path
) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    expect(page.locator("#figure-caption")).to_contain_text("Wald reconstruction")
    expect(page.locator("#copy-caption")).to_be_visible()

    for mode in ("both", "likelihood"):
        if mode != "both":
            page.locator(f"#view-mode-{mode}").check()
            page.wait_for_function(
                """
                (expectedMode) => {
                  const plot = document.getElementById("curve-plot");
                  return plot?.dataset?.viewMode === expectedMode;
                }
                """,
                arg=mode,
                timeout=120000,
            )

        with page.expect_download() as download_info:
            page.locator("#export-manuscript-png").click()
        download = download_info.value

        assert download.suggested_filename == "wald-confidence-curves-manuscript.png"
        png_path = tmp_path / f"{mode}-{download.suggested_filename}"
        download.save_as(png_path)
        assert png_path.stat().st_size > 0

    expect(page.locator("#figure-caption")).to_contain_text(
        "not exact fitted-model profile likelihood"
    )


def test_desktop_sidebar_can_collapse_and_restore(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    initial_widths = plot_width_metrics(page)

    page.locator("#desktop-controls-toggle").click()
    expect(page.locator(".page-shell")).to_have_attribute("data-controls-collapsed", "true")
    expect(page.locator("#controls-panel")).to_be_hidden()
    page.wait_for_function(
        """
        (initialSurface) => {
          const plot = document.getElementById("curve-plot");
          const surface = plot.getBoundingClientRect();
          const svg = plot.querySelector(".main-svg")?.getBoundingClientRect();
          return svg
            && surface.width > initialSurface
            && Math.abs(svg.width - surface.width) < 2;
        }
        """,
        arg=initial_widths["surface"],
        timeout=120000,
    )
    collapsed_widths = plot_width_metrics(page)
    assert collapsed_widths["surface"] > initial_widths["surface"]
    assert collapsed_widths["svg"] == pytest.approx(collapsed_widths["surface"], abs=2)

    page.locator("#desktop-controls-toggle").click()
    expect(page.locator(".page-shell")).to_have_attribute("data-controls-collapsed", "false")
    expect(page.locator("#controls-panel")).to_be_visible()
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          const surface = plot.getBoundingClientRect();
          const svg = plot.querySelector(".main-svg")?.getBoundingClientRect();
          return svg && Math.abs(svg.width - surface.width) < 2;
        }
        """,
        timeout=120000,
    )


def test_mobile_controls_toggle_remains_usable(app_url: str, page: Page) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(app_url)
    wait_for_ready(page)

    toggle = page.locator("#controls-toggle")
    toggle.click()
    expect(page.locator("#controls-panel")).to_have_attribute("data-collapsed", "true")
    toggle.click()
    expect(page.locator("#controls-panel")).to_have_attribute("data-collapsed", "false")
