from __future__ import annotations

from pathlib import Path

import pytest
from helpers import open_advanced_options, wait_for_ready, xaxis_bounds
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


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
