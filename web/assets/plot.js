const GUIDE_LEVELS = [0.1, 0.05, 0.01];

function formatHoverNumber(value) {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  const magnitude = Math.abs(value);
  if (magnitude >= 1_000 || (magnitude > 0 && magnitude < 0.001)) {
    return value.toExponential(3);
  }
  return value.toFixed(4);
}

function makeVerticalShapes(response) {
  const thresholds = response.meta.thresholds_display ?? [];
  const criticalMarkers = response.summary.critical_effect_markers_display ?? [];
  const markers = [
    {
      value: response.summary.estimate_display,
      color: "#b04a2f",
      dash: "solid",
      width: 3,
    },
    {
      value: response.summary.null_display,
      color: "#132a3a",
      dash: "dot",
      width: 2,
    },
    ...criticalMarkers.map((value) => ({
      value,
      color: "#8f6b1f",
      dash: "dashdot",
      width: 2,
    })),
    ...thresholds.map((value) => ({
      value,
      color: "#4c8a5b",
      dash: "dash",
      width: 3,
    })),
  ];

  return markers.map((marker) => ({
    type: "line",
    xref: "x",
    yref: "paper",
    x0: marker.value,
    x1: marker.value,
    y0: 0,
    y1: 1,
    line: {
      color: marker.color,
      dash: marker.dash,
      width: marker.width,
    },
    layer: "below",
  }));
}

function makeGuideShapes(response) {
  if (!response.meta.show_cutoffs) {
    return [];
  }

  const xValues = response.grid.effect_display;
  return GUIDE_LEVELS.map((level) => ({
    type: "line",
    xref: "x",
    yref: "y",
    x0: xValues[0],
    x1: xValues[xValues.length - 1],
    y0: level,
    y1: level,
    line: {
      color: "rgba(19, 42, 58, 0.28)",
      dash: "dash",
      width: 1.5,
    },
    layer: "below",
  }));
}

function axisTitle(response) {
  const label = response.meta.effect_spec.label;
  return response.meta.effect_spec.family === "ratio" ? `${label} (natural scale)` : label;
}

function axisType(response, displayOptions) {
  return response.meta.effect_spec.family === "ratio" && displayOptions.axisSpacing === "log"
    ? "log"
    : "linear";
}

export async function renderCurves(plotElement, response, displayOptions) {
  const nullRelativeLikelihood = response.summary.null_relative_likelihood;
  const likelihoodRatioVsNull = response.grid.relative_likelihood.map((value) =>
    nullRelativeLikelihood === 0 ? Number.POSITIVE_INFINITY : value / nullRelativeLikelihood,
  );
  const xAxisType = axisType(response, displayOptions);
  const previousAxisType = plotElement._fullLayout?.xaxis?.type || "linear";

  if (previousAxisType !== xAxisType) {
    Plotly.purge(plotElement);
    plotElement.innerHTML = "";
  }

  const topTrace = {
    type: "scatter",
    mode: "lines",
    x: response.grid.effect_display,
    y: response.grid.compatibility,
    xaxis: "x",
    yaxis: "y",
    line: {
      color: "#b04a2f",
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
    name: "Compatibility curve",
    showlegend: false,
  };

  const bottomTrace = {
    type: "scatter",
    mode: "lines",
    x: response.grid.effect_display,
    y: response.grid.relative_likelihood,
    xaxis: "x2",
    yaxis: "y2",
    line: {
      color: "#132a3a",
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
  };

  const layout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(255, 252, 247, 0.65)",
    margin: { l: 92, r: 30, t: 18, b: 60 },
    hovermode: "closest",
    xaxis: {
      title: {
        text: axisTitle(response),
        standoff: 12,
      },
      anchor: "y",
      type: xAxisType,
      autorange: true,
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    },
    yaxis: {
      title: {
        text: "Compatibility",
        standoff: 12,
      },
      domain: [0.56, 1],
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    },
    xaxis2: {
      title: {
        text: axisTitle(response),
        standoff: 12,
      },
      anchor: "y2",
      matches: "x",
      type: xAxisType,
      autorange: true,
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    },
    yaxis2: {
      title: {
        text: "Relative likelihood",
        standoff: 12,
      },
      domain: [0, 0.42],
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    },
    shapes: [...makeVerticalShapes(response), ...makeGuideShapes(response)],
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      "lasso2d",
      "select2d",
      "autoScale2d",
      "hoverCompareCartesian",
      "toggleSpikelines",
    ],
  };

  await Plotly.react(plotElement, [topTrace, bottomTrace], layout, config);
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
