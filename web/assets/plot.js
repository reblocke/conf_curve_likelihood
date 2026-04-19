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

function makeGuideShapes(response, viewMode) {
  if (!response.meta.show_cutoffs || viewMode === "likelihood") {
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

function formatAxisTick(value) {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  return new Intl.NumberFormat("en-US", {
    maximumSignificantDigits: 3,
  }).format(value);
}

function roundToSignificantDigits(value, digits) {
  if (!Number.isFinite(value) || value === 0) {
    return value;
  }
  return Number.parseFloat(value.toPrecision(digits));
}

function deduplicateSortedValues(values) {
  return [...values]
    .filter((value) => Number.isFinite(value) && value > 0)
    .sort((left, right) => left - right)
    .filter((value, index, sortedValues) => {
      if (index === 0) {
        return true;
      }
      const previousValue = sortedValues[index - 1];
      return Math.abs(value - previousValue) > Math.max(1e-12, Math.abs(value) * 1e-9);
    });
}

function logTickMantissas(logSpan) {
  if (logSpan <= 0.35) {
    return [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8];
  }
  if (logSpan <= 1.1) {
    return [1, 2, 3, 4, 5, 6, 8];
  }
  if (logSpan <= 2.5) {
    return [1, 2, 5];
  }
  return [1];
}

function fallbackLogTickValues(lowerBound, upperBound) {
  const tickCount = 4;
  const growthFactor = Math.pow(upperBound / lowerBound, 1 / (tickCount - 1));
  return Array.from({ length: tickCount }, (_, index) =>
    roundToSignificantDigits(lowerBound * Math.pow(growthFactor, index), 2),
  );
}

function logAxisTickConfig(xValues) {
  const finitePositiveValues = xValues.filter((value) => Number.isFinite(value) && value > 0);
  if (finitePositiveValues.length < 2) {
    return {};
  }

  const lowerBound = finitePositiveValues[0];
  const upperBound = finitePositiveValues[finitePositiveValues.length - 1];
  if (!(lowerBound < upperBound)) {
    return {};
  }

  const logSpan = Math.log10(upperBound) - Math.log10(lowerBound);
  const candidateTickValues = [];
  const mantissas = logTickMantissas(logSpan);
  const startExponent = Math.floor(Math.log10(lowerBound));
  const endExponent = Math.ceil(Math.log10(upperBound));

  for (let exponent = startExponent; exponent <= endExponent; exponent += 1) {
    const scale = 10 ** exponent;
    for (const mantissa of mantissas) {
      const tickValue = mantissa * scale;
      if (tickValue < lowerBound * 0.999999 || tickValue > upperBound * 1.000001) {
        continue;
      }
      candidateTickValues.push(roundToSignificantDigits(tickValue, 6));
    }
  }

  if (lowerBound <= 1 && upperBound >= 1) {
    candidateTickValues.push(1);
  }

  const tickvals = deduplicateSortedValues(
    candidateTickValues.length >= 3
      ? candidateTickValues
      : [...candidateTickValues, ...fallbackLogTickValues(lowerBound, upperBound)],
  );

  return {
    tickmode: "array",
    tickvals,
    ticktext: tickvals.map((value) => formatAxisTick(value)),
  };
}

function explicitAxisRange(response, xAxisType) {
  const displayRange = response.meta.display_range_display;
  if (!response.meta.display_range_active || !Array.isArray(displayRange)) {
    return { autorange: true };
  }

  const [lowerBound, upperBound] = displayRange;
  if (!Number.isFinite(lowerBound) || !Number.isFinite(upperBound) || lowerBound >= upperBound) {
    return { autorange: true };
  }
  if (xAxisType === "log") {
    if (lowerBound <= 0 || upperBound <= 0) {
      return { autorange: true };
    }
    return {
      autorange: false,
      range: [Math.log10(lowerBound), Math.log10(upperBound)],
    };
  }

  return {
    autorange: false,
    range: [lowerBound, upperBound],
  };
}

export async function renderCurves(plotElement, response, displayOptions) {
  const viewMode = displayOptions.viewMode ?? "both";
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
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(255, 252, 247, 0.65)",
    margin: { l: 92, r: 30, t: 18, b: 60 },
    hovermode: "closest",
    xaxis: {
      ...xAxisLayout,
      anchor: "y",
    },
    yaxis: {
      title: {
        text:
          viewMode === "likelihood" ? "Relative likelihood" : "Compatibility / confidence curve",
        standoff: 12,
      },
      domain: viewMode === "both" ? [0.56, 1] : [0, 1],
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    },
    shapes: [...makeVerticalShapes(response), ...makeGuideShapes(response, viewMode)],
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
      domain: [0, 0.42],
      range: [0, 1.02],
      automargin: true,
      showgrid: true,
      gridcolor: "rgba(19, 42, 58, 0.08)",
      zeroline: false,
    };
  }

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
