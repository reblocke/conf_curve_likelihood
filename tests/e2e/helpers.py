from __future__ import annotations

from playwright.sync_api import Page, expect


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


def x_axis_titles(page: Page) -> list[str]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => Array.from(element.querySelectorAll(".g-xtitle text, .g-x2title text"))
          .map((node) => node.textContent?.trim())
          .filter(Boolean)
        """
    )


def x_axis_ticklabel_visibility(page: Page) -> dict[str, bool | None]:
    return page.locator("#curve-plot").evaluate(
        """
        (element) => ({
          xaxis: element._fullLayout.xaxis?.showticklabels,
          xaxis2: element._fullLayout.xaxis2?.showticklabels,
        })
        """
    )


def annotation_overlaps_x_axis_title(page: Page, annotation_text: str) -> bool:
    return page.locator("#curve-plot").evaluate(
        """
        (element, expectedText) => {
          const annotation = Array.from(element.querySelectorAll(".annotation-text"))
            .find((node) => node.textContent?.trim() === expectedText);
          const titles = Array.from(element.querySelectorAll(".g-xtitle text, .g-x2title text"))
            .filter((node) => node.textContent?.trim());
          if (!annotation || titles.length === 0) {
            return false;
          }

          const annotationBox = annotation.getBoundingClientRect();
          return titles.some((title) => {
            const titleBox = title.getBoundingClientRect();
            return !(
              annotationBox.right <= titleBox.left ||
              annotationBox.left >= titleBox.right ||
              annotationBox.bottom <= titleBox.top ||
              annotationBox.top >= titleBox.bottom
            );
          });
        }
        """,
        annotation_text,
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
