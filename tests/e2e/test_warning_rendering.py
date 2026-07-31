from __future__ import annotations

import pytest
from helpers import wait_for_ready
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def test_warning_messages_render_as_inert_text(app_url: str, page: Page) -> None:
    page.goto(app_url)
    wait_for_ready(page)

    design_warning = '<img src=x onerror="window.__warningXssExecuted = true"> design warning'
    response_warning = '<svg onload="window.__warningXssExecuted = true">response warning</svg>'
    result = page.evaluate(
        """
        async ([designWarning, responseWarning]) => {
          window.__warningXssExecuted = false;
          const { renderWarnings } = await import("./assets/renderers.js");
          const warningsList = document.getElementById("warnings-list");

          renderWarnings(
            {
              meta: {
                effect_spec: { family: "additive" },
                se_method: "synthetic-test",
                thresholds_display: [],
                display_range_active: false,
                display_range_display: null,
                show_cutoffs: false,
              },
              design: {
                config: { enabled: true },
                grid: {
                  type_m: [],
                  observed_exaggeration: [],
                },
                warnings: [designWarning],
              },
              warnings: [responseWarning],
            },
            { axisSpacing: "linear", viewMode: "both" },
            warningsList,
          );

          await new Promise((resolve) => setTimeout(resolve, 100));
          return {
            executed: window.__warningXssExecuted,
            childTags: Array.from(warningsList.children, (child) => child.tagName),
            maliciousElementCount: warningsList.querySelectorAll("img, svg, script").length,
            messages: Array.from(warningsList.children, (child) => child.textContent),
          };
        }
        """,
        [design_warning, response_warning],
    )

    assert result["executed"] is False
    assert result["maliciousElementCount"] == 0
    assert result["childTags"] and set(result["childTags"]) == {"LI"}
    assert result["messages"][-2:] == [design_warning, response_warning]
