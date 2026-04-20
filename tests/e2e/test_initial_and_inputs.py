from __future__ import annotations

import pytest
from helpers import (
    open_advanced_options,
    paper_shape_x_values,
    wait_for_ready,
    xaxis_pixel_positions,
    xaxis_tick_labels,
    xaxis_type,
    xaxis_upper_bound,
)
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


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
