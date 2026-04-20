from __future__ import annotations

from pathlib import Path

import pytest
from helpers import plot_width_metrics, wait_for_ready
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


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
