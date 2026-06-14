import { designMetricOptionForKey } from "./config.js";
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
  panelDomains,
} from "./plot-helpers.js";

const DESIGN_RATIO_DISPLAY_CAP = 10;
const DESIGN_RATIO_GUIDE_VALUE = 2;
const DESIGN_RATIO_TICK_VALUES = [0, 1, 2, 5, 10];
const DESIGN_PANEL_SPECS = [
  {
    key: "power",
    axisId: "3",
    color: "#4c8a5b",
    cap: null,
  },
  {
    key: "type_s",
    axisId: "4",
    color: "#7a4f9a",
    cap: null,
  },
  {
    key: "type_m",
    axisId: "5",
    color: "#8f6b1f",
    cap: DESIGN_RATIO_DISPLAY_CAP,
  },
  {
    key: "observed_exaggeration",
    axisId: "6",
    color: "#2f6f8f",
    cap: DESIGN_RATIO_DISPLAY_CAP,
  },
];

function hasDesign(response) {
  return response.design?.config?.enabled === true;
}

function formatOptionalHoverNumber(value) {
  if (value === null || value === undefined) {
    return "undefined near null";
  }
  return formatHoverNumber(value);
}

function designMetricLabel(metricKey) {
  return designMetricOptionForKey(metricKey).label;
}

function designMetricField(metricKey) {
  return designMetricOptionForKey(metricKey).field;
}

function designMetricValues(response, metricKey, cap = null) {
  const field = designMetricField(metricKey);
  return response.design.grid[field].map((value) => {
    if (value === null || value === undefined) {
      return null;
    }
    if (!Number.isFinite(value)) {
      return null;
    }
    if (cap !== null && value > cap) {
      return null;
    }
    return value;
  });
}

function designYAxisTitle(metricKey) {
  if (metricKey === "power") {
    return "Power";
  }
  if (metricKey === "type_s") {
    return "Type S probability";
  }
  if (metricKey === "type_m") {
    return "Type M (x-fold exaggeration)";
  }
  return "Observed ratio (x-fold)";
}

function ratioYAxisRange(values) {
  const finiteValues = values.filter((value) => Number.isFinite(value));
  if (finiteValues.length === 0) {
    return [0, DESIGN_RATIO_DISPLAY_CAP];
  }
  const maxValue = Math.max(...finiteValues);
  const paddedMax = Math.min(DESIGN_RATIO_DISPLAY_CAP, Math.max(1.05, maxValue * 1.08));
  return [0, paddedMax];
}

function designYAxisOptions(metricKey, values, cap = null) {
  if (metricKey === "power" || metricKey === "type_s") {
    return { range: [0, 1.02] };
  }
  if (cap !== null) {
    const range = ratioYAxisRange(values);
    const tickvals = DESIGN_RATIO_TICK_VALUES.filter((value) => value <= range[1] + 1e-9);
    return {
      range,
      tickmode: "array",
      tickvals,
      ticktext: tickvals.map((value) => (value === 0 ? "0" : `${value}x`)),
    };
  }
  return { rangemode: "tozero" };
}

function makeDesignRatioGuideShapes(response, spec, values) {
  if (spec.cap === null || ratioYAxisRange(values)[1] < DESIGN_RATIO_GUIDE_VALUE) {
    return [];
  }
  const xValues = response.design.grid.true_effect_display.filter((value) => Number.isFinite(value));
  if (xValues.length < 2) {
    return [];
  }
  return [
    {
      type: "line",
      xref: `x${spec.axisId}`,
      yref: `y${spec.axisId}`,
      x0: xValues[0],
      x1: xValues[xValues.length - 1],
      y0: DESIGN_RATIO_GUIDE_VALUE,
      y1: DESIGN_RATIO_GUIDE_VALUE,
      line: {
        color: "rgba(19, 42, 58, 0.22)",
        dash: "dot",
        width: 1.25,
      },
      layer: "below",
    },
  ];
}

function makeDesignSeparatorShape(designEnabled, domains) {
  if (!designEnabled) {
    return [];
  }
  return [
    {
      type: "line",
      xref: "paper",
      yref: "paper",
      x0: 0,
      x1: 1,
      y0: domains.separatorY,
      y1: domains.separatorY,
      line: {
        color: "rgba(19, 42, 58, 0.22)",
        width: 1,
      },
      layer: "above",
    },
  ];
}

function makeDesignRangeShapes(response, xref, yref) {
  const range = response.design?.config?.plausible_range_display;
  if (!Array.isArray(range) || range.length !== 2) {
    return [];
  }
  const [lower, upper] = range;
  if (!Number.isFinite(lower) || !Number.isFinite(upper) || lower >= upper) {
    return [];
  }
  return [
    {
      type: "rect",
      xref,
      yref: `${yref} domain`,
      x0: lower,
      x1: upper,
      y0: 0,
      y1: 1,
      fillcolor: "rgba(76, 138, 91, 0.08)",
      line: {
        color: "rgba(76, 138, 91, 0.2)",
        width: 1,
      },
      layer: "below",
    },
  ];
}

export async function renderCurves(plotElement, response, displayOptions) {
  const viewMode = displayOptions.viewMode ?? "both";
  const manuscript = displayOptions.manuscript === true;
  const designEnabled = hasDesign(response);
  const domains = panelDomains(viewMode, designEnabled);
  const nullRelativeLikelihood = response.summary.null_relative_likelihood;
  const likelihoodRatioVsNull = response.grid.relative_likelihood.map((value) =>
    nullRelativeLikelihood === 0 ? Number.POSITIVE_INFINITY : value / nullRelativeLikelihood,
  );
  const xAxisType = axisType(response, displayOptions);
  const xAxisTicks = xAxisType === "log" ? logAxisTickConfig(response.grid.effect_display) : {};
  const xAxisRange = explicitAxisRange(response, xAxisType);
  const previousAxisType = plotElement._fullLayout?.xaxis?.type || "linear";
  const previousViewMode = plotElement.dataset.viewMode || "both";
  const previousDesignEnabled = plotElement.dataset.designEnabled === "true";

  if (
    previousAxisType !== xAxisType ||
    previousViewMode !== viewMode ||
    previousDesignEnabled !== designEnabled
  ) {
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

  const makeDesignTrace = (spec, values) => ({
    type: "scatter",
    mode: "lines",
    x: response.design.grid.true_effect_display,
    y: values,
    xaxis: `x${spec.axisId}`,
    yaxis: `y${spec.axisId}`,
    connectgaps: false,
    line: {
      color: spec.color,
      dash: "solid",
      width: 3,
    },
    hovertemplate:
      "<b>Assume this x-value is the true effect</b>: %{x}<br>" +
      "Observed compatibility p-value: %{customdata[0]}<br>" +
      "Relative likelihood vs estimate: %{customdata[1]}<br>" +
      "Claim rule: %{customdata[6]}<br>" +
      "Information multiplier: %{customdata[7]}<br>" +
      "Power: %{customdata[2]}<br>" +
      "Type S: %{customdata[3]}<br>" +
      "Type M: %{customdata[4]}<br>" +
      "Observed exaggeration: %{customdata[5]}<extra></extra>",
    customdata: response.grid.compatibility.map((compatibility, index) => [
      formatHoverNumber(compatibility),
      formatHoverNumber(response.grid.relative_likelihood[index]),
      formatHoverNumber(response.design.grid.power[index]),
      formatOptionalHoverNumber(response.design.grid.type_s[index]),
      formatOptionalHoverNumber(response.design.grid.type_m[index]),
      formatOptionalHoverNumber(response.design.grid.observed_exaggeration[index]),
      response.design.config.selection_rule_label,
      formatHoverNumber(response.design.config.information_multiplier),
    ]),
    name: designMetricLabel(spec.key),
    showlegend: false,
  });

  const xAxisLayout = {
    title: {
      text: axisTitle(response, designEnabled),
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
    margin: {
      l: manuscript ? 110 : 92,
      r: manuscript ? 70 : 36,
      t: 96,
      b: manuscript ? 78 : 66,
    },
    hovermode: "closest",
    xaxis: {
      ...xAxisLayout,
      anchor: "y",
      ...(viewMode === "both" || designEnabled
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
      domain:
        viewMode === "both"
          ? domains.primary
          : domains.primary,
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    },
    shapes: [
      ...makeIntervalShapes(response, viewMode),
      ...makeVerticalShapes(response, { viewMode, designEnabled }),
      ...makeGuideShapes(response, viewMode),
      ...makeDesignSeparatorShape(designEnabled, domains),
      ...(designEnabled
        ? DESIGN_PANEL_SPECS.flatMap((spec) =>
            makeDesignRangeShapes(response, `x${spec.axisId}`, `y${spec.axisId}`),
          )
        : []),
    ],
    annotations: [
      ...makePanelAnnotations(viewMode, manuscript, designEnabled),
      ...makeIntervalAnnotations(response, viewMode, xAxisType, manuscript, designEnabled),
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
      ...(designEnabled
        ? {
            title: { text: "" },
            showticklabels: false,
            ticks: "",
          }
        : {}),
    };
    layout.yaxis2 = {
      title: {
        text: "Relative likelihood",
        standoff: 12,
      },
      domain: domains.secondary,
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    };
  }
  if (designEnabled) {
    for (const spec of DESIGN_PANEL_SPECS) {
      const values = designMetricValues(response, spec.key, spec.cap);
      const isBottomDesignPanel = spec.axisId === "6";
      const yAxisTitle = {
        text: designYAxisTitle(spec.key),
        standoff: 12,
        ...(spec.cap === null ? {} : { font: { size: manuscript ? 13 : 11 } }),
      };
      traces.push(makeDesignTrace(spec, values));
      layout.shapes.push(...makeDesignRatioGuideShapes(response, spec, values));
      layout[`xaxis${spec.axisId}`] = {
        ...xAxisLayout,
        anchor: `y${spec.axisId}`,
        matches: "x",
        ...(isBottomDesignPanel
          ? {}
          : {
              title: { text: "" },
              showticklabels: false,
              ticks: "",
            }),
      };
      layout[`yaxis${spec.axisId}`] = {
        title: yAxisTitle,
        domain: domains.design[spec.axisId],
        automargin: true,
        showgrid: true,
        gridcolor: "rgba(19, 42, 58, 0.08)",
        zeroline: false,
        ...designYAxisOptions(spec.key, values, spec.cap),
      };
    }
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

  plotElement.dataset.designEnabled = String(designEnabled);
  await Plotly.react(plotElement, traces, layout, config);
  plotElement.dataset.viewMode = viewMode;
}

export async function exportPlotPng(plotElement, filename) {
  const height = plotElement.dataset.designEnabled === "true" ? 1600 : 1100;
  const dataUrl = await Plotly.toImage(plotElement, {
    format: "png",
    height,
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
  const exportHeight = hasDesign(response) ? 1500 : 1000;
  exportElement.style.position = "fixed";
  exportElement.style.left = "-10000px";
  exportElement.style.top = "0";
  exportElement.style.width = "1400px";
  exportElement.style.height = `${exportHeight}px`;
  document.body.append(exportElement);

  try {
    await renderCurves(exportElement, response, {
      ...displayOptions,
      manuscript: true,
    });
    const dataUrl = await Plotly.toImage(exportElement, {
      format: "png",
      height: exportHeight,
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
