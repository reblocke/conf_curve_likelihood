from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def wait_for_ready(page: Page) -> None:
    expect(page.locator("#status-card")).to_contain_text("Curves updated", timeout=120000)


def test_initial_render_loads_pyodide_and_plots(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    expect(page.locator("#summary-grid")).to_contain_text("Working-scale SE")
    expect(page.locator("#commentary-text")).to_contain_text("Wald approximation")
    expect(page.locator("#curve-plot .main-svg").first).to_be_visible()


def test_effect_type_switch_updates_controls(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.select_option("#effect-type", "mean_difference")
    page.locator("#estimate").fill("0.42")
    page.locator("#ci-lower").fill("0.11")
    page.locator("#ci-upper").fill("0.73")
    wait_for_ready(page)

    expect(page.locator("#display-natural-axis")).to_be_disabled()
    expect(page.locator("#null-value")).to_have_value("0")


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

    page.locator("#thresholds").fill("0.8, 1.25")
    wait_for_ready(page)

    shape_count = page.locator("#curve-plot").evaluate(
        "(element) => element._fullLayout.shapes.length"
    )
    assert shape_count >= 4


def test_distant_markers_expand_the_x_axis_extent(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    page.locator("#null-value").fill("12")
    page.locator("#thresholds").fill("8")
    page.wait_for_function(
        """
        () => {
          const plot = document.getElementById("curve-plot");
          return plot?._fullLayout?.xaxis?.range?.[1] > 12;
        }
        """,
        timeout=120000,
    )

    x_axis_range = page.locator("#curve-plot").evaluate(
        "(element) => element._fullLayout.xaxis.range"
    )
    assert x_axis_range[1] > 12


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


def test_mobile_controls_toggle_remains_usable(app_url: str, page: Page) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(app_url)
    wait_for_ready(page)

    toggle = page.locator("#controls-toggle")
    toggle.click()
    expect(page.locator("#controls-panel")).to_have_attribute("data-collapsed", "true")
    toggle.click()
    expect(page.locator("#controls-panel")).to_have_attribute("data-collapsed", "false")
