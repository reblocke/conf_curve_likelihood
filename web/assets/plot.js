import {
  axisTitle,
  axisType,
  explicitAxisRange,
  formatHoverNumber,
  logAxisTickConfig,
  makeDirectLabelAnnotations,
  makeGuideShapes,
  makeIntervalAnnotations,
  makeIntervalShapes,
  makePanelAnnotations,
  makeVerticalShapes,
} from "./plot-helpers.js";

export async function renderCurves(plotElement, response, displayOptions) {
  const viewMode = displayOptions.viewMode ?? "both";
  const manuscript = displayOptions.manuscript === true;
  const nullRelativeLikelihood = response.summary.null_relative_likelihood;
  const likelihoodRatioVsNull = response.grid.relative_likelihood.map((value) =>
    nullRelativeLikelihood === 0 ? Number.POSITIVE_INFINITY : value / nullRelativeLikelihood,
  );
  const xAxisType = axisType(response, displayOptions);
  const xAxisTicks = xAxisType === "log" ? logAxisTickConfig(response.grid.effect_display) : {};
  const xAxisRange = explicitAxisRange(response, xAxisType);
  const previousAxisType = plotElement._fullLayout?.xaxis?.type || "linear";
  const previousViewMode = plotElement.dataset.viewMode || "both";

  if (previousAxisType !== xAxisType || previousViewMode !== viewMode) {
    Plotly.purge(plotElement);
    plotElement.innerHTML = "";
  }

  const makeCompatibilityTrace = (xaxis, yaxis) => ({
    type: "scatter",
    mode: "lines",
    x: response.grid.effect_display,
    y: response.grid.compatibility,
    xaxis,
    yaxis,
    line: {
      color: "#b04a2f",
      dash: manuscript ? "solid" : "solid",
      width: 3,
    },
    hovertemplate:
      "<b>Effect size</b>: %{x}<br>" +
      "Working-scale effect: %{customdata[0]}<br>" +
      "Compatibility: %{customdata[1]}<br>" +
      "%{customdata[2]}<extra></extra>",
    customdata: response.grid.effect_working.map((workingValue, index) => [
      formatHoverNumber(workingValue),
      formatHoverNumber(response.grid.compatibility[index]),
      response.grid.compatibility[index] >= 0.05 ? "Inside 95% CI" : "Outside 95% CI",
    ]),
    name: "Compatibility / confidence curve",
    showlegend: false,
  });

  const makeLikelihoodTrace = (xaxis, yaxis) => ({
    type: "scatter",
    mode: "lines",
    x: response.grid.effect_display,
    y: response.grid.relative_likelihood,
    xaxis,
    yaxis,
    line: {
      color: "#132a3a",
      dash: manuscript ? "dash" : "solid",
      width: 3,
    },
    hovertemplate:
      "<b>Effect size</b>: %{x}<br>" +
      "Working-scale effect: %{customdata[0]}<br>" +
      "Relative likelihood: %{customdata[1]}<br>" +
      "Log relative likelihood: %{customdata[2]}<br>" +
      "Likelihood ratio versus null: %{customdata[3]}<extra></extra>",
    customdata: response.grid.effect_working.map((workingValue, index) => [
      formatHoverNumber(workingValue),
      formatHoverNumber(response.grid.relative_likelihood[index]),
      formatHoverNumber(response.grid.log_relative_likelihood[index]),
      formatHoverNumber(likelihoodRatioVsNull[index]),
    ]),
    name: "Relative likelihood curve",
    showlegend: false,
  });

  const xAxisLayout = {
    title: {
      text: axisTitle(response),
      standoff: 12,
    },
    type: xAxisType,
    ...xAxisRange,
    automargin: true,
    showgrid: true,
    gridcolor: "rgba(19, 42, 58, 0.08)",
    zeroline: false,
    ...xAxisTicks,
  };
  const layout = {
    paper_bgcolor: manuscript ? "#ffffff" : "rgba(0,0,0,0)",
    plot_bgcolor: manuscript ? "#ffffff" : "rgba(255, 252, 247, 0.65)",
    font: {
      family: '"Avenir Next", "Segoe UI", Arial, sans-serif',
      size: manuscript ? 15 : 13,
      color: "#132a3a",
    },
    margin: { l: manuscript ? 110 : 92, r: manuscript ? 70 : 36, t: 96, b: manuscript ? 78 : 66 },
    hovermode: "closest",
    xaxis: {
      ...xAxisLayout,
      anchor: "y",
      ...(viewMode === "both"
        ? {
            title: { text: "" },
            showticklabels: false,
            ticks: "",
          }
        : {}),
    },
    yaxis: {
      title: {
        text:
          viewMode === "likelihood" ? "Relative likelihood" : "Compatibility / confidence curve",
        standoff: 12,
      },
      domain: viewMode === "both" ? [0.58, 1] : [0, 1],
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    },
    shapes: [
      ...makeIntervalShapes(response, viewMode),
      ...makeVerticalShapes(response),
      ...makeGuideShapes(response, viewMode),
    ],
    annotations: [
      ...makePanelAnnotations(viewMode, manuscript),
      ...makeIntervalAnnotations(response, viewMode, xAxisType, manuscript),
      ...makeDirectLabelAnnotations(response, displayOptions, xAxisType),
    ],
  };
  let traces;
  if (viewMode === "likelihood") {
    traces = [makeLikelihoodTrace("x", "y")];
  } else if (viewMode === "compatibility") {
    traces = [makeCompatibilityTrace("x", "y")];
  } else {
    traces = [makeCompatibilityTrace("x", "y"), makeLikelihoodTrace("x2", "y2")];
    layout.xaxis2 = {
      ...xAxisLayout,
      anchor: "y2",
      matches: "x",
    };
    layout.yaxis2 = {
      title: {
        text: "Relative likelihood",
        standoff: 12,
      },
      domain: [0, 0.4],
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    };
  }

  const config = {
    responsive: !manuscript,
    displaylogo: false,
    modeBarButtonsToRemove: [
      "lasso2d",
      "select2d",
      "autoScale2d",
      "hoverCompareCartesian",
      "toggleSpikelines",
    ],
  };

  await Plotly.react(plotElement, traces, layout, config);
  plotElement.dataset.viewMode = viewMode;
}

export async function exportPlotPng(plotElement, filename) {
  const dataUrl = await Plotly.toImage(plotElement, {
    format: "png",
    height: 1100,
    width: 1400,
    scale: 2,
  });
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = filename;
  link.click();
}

export async function exportManuscriptPng(response, displayOptions, filename) {
  const exportElement = document.createElement("div");
  exportElement.style.position = "fixed";
  exportElement.style.left = "-10000px";
  exportElement.style.top = "0";
  exportElement.style.width = "1400px";
  exportElement.style.height = "1000px";
  document.body.append(exportElement);

  try {
    await renderCurves(exportElement, response, {
      ...displayOptions,
      manuscript: true,
    });
    const dataUrl = await Plotly.toImage(exportElement, {
      format: "png",
      height: 1000,
      width: 1400,
      scale: 2,
    });
    const link = document.createElement("a");
    link.href = dataUrl;
    link.download = filename;
    link.click();
  } finally {
    Plotly.purge(exportElement);
    exportElement.remove();
  }
}
