from __future__ import annotations

import pytest
from helpers import (
    horizontal_cutoff_count,
    open_advanced_options,
    plot_annotation_texts,
    plot_trace_names,
    wait_for_ready,
    xaxis_bounds,
    y_axis_titles,
)
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


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
