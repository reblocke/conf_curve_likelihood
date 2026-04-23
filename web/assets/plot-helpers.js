const GUIDE_LEVELS = [0.1, 0.05, 0.01];
const REFERENCE_STYLES = {
  estimate: {
    color: "#b04a2f",
    dash: "solid",
    width: 3,
  },
  null: {
    color: "#132a3a",
    dash: "dot",
    width: 2,
  },
  critical: {
    color: "#8f6b1f",
    dash: "dashdot",
    width: 2,
  },
  threshold: {
    color: "#4c8a5b",
    dash: "dash",
    width: 3,
  },
};
const INTERVAL_STYLES = {
  ci: {
    fillcolor: "rgba(176, 74, 47, 0.08)",
    lineColor: "rgba(176, 74, 47, 0.22)",
    labelColor: "#8f3f2b",
  },
  sMinus2: {
    fillcolor: "rgba(19, 42, 58, 0.07)",
    lineColor: "rgba(19, 42, 58, 0.42)",
    labelColor: "#132a3a",
  },
};

export function formatHoverNumber(value) {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  const magnitude = Math.abs(value);
  if (magnitude >= 1_000 || (magnitude > 0 && magnitude < 0.001)) {
    return value.toExponential(3);
  }
  return value.toFixed(4);
}

function formatAxisTick(value) {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  return new Intl.NumberFormat("en-US", {
    maximumSignificantDigits: 3,
  }).format(value);
}

function makeReferenceMarkers(response) {
  const thresholds = response.meta.thresholds_display ?? [];
  const criticalMarkers = response.summary.critical_effect_markers_display ?? [];
  return [
    {
      key: "estimate",
      value: response.summary.estimate_display,
      label: "Estimate",
    },
    {
      key: "null",
      value: response.summary.null_display,
      label: "Null",
    },
    ...criticalMarkers.map((value) => ({
      key: "critical",
      value,
      label: "Design threshold",
    })),
    ...thresholds.map((value) => ({
      key: "threshold",
      value,
      label: `Threshold ${formatAxisTick(value)}`,
    })),
  ];
}

export function makeVerticalShapes(response) {
  return makeReferenceMarkers(response).map((marker) => ({
    type: "line",
    xref: "x",
    yref: "paper",
    x0: marker.value,
    x1: marker.value,
    y0: 0,
    y1: 1,
    line: {
      color: REFERENCE_STYLES[marker.key].color,
      dash: REFERENCE_STYLES[marker.key].dash,
      width: REFERENCE_STYLES[marker.key].width,
    },
    layer: "below",
  }));
}

export function makeGuideShapes(response, viewMode) {
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

function hasCompatibilityPanel(viewMode) {
  return viewMode !== "likelihood";
}

function hasLikelihoodPanel(viewMode) {
  return viewMode !== "compatibility";
}

function validInterval(values) {
  if (!Array.isArray(values) || values.length !== 2) {
    return null;
  }
  const lower = Number(values[0]);
  const upper = Number(values[1]);
  if (!Number.isFinite(lower) || !Number.isFinite(upper) || lower > upper) {
    return null;
  }
  return [lower, upper];
}

function clippedVisibleInterval(values, response) {
  const interval = validInterval(values);
  if (interval === null) {
    return null;
  }
  const [visibleLower, visibleUpper] = visibleRange(response);
  const lower = Math.max(interval[0], visibleLower);
  const upper = Math.min(interval[1], visibleUpper);
  return lower <= upper ? [lower, upper] : null;
}

function intervalMidpoint(interval, xAxisType) {
  const [lower, upper] = interval;
  if (xAxisType === "log") {
    if (lower <= 0 || upper <= 0) {
      return Number.NaN;
    }
    return 10 ** ((Math.log10(lower) + Math.log10(upper)) / 2);
  }
  return (lower + upper) / 2;
}

function normalizedXPosition(value, response, xAxisType) {
  const [lowerBound, upperBound] = visibleRange(response);
  const lowerPosition = valuePosition(lowerBound, xAxisType);
  const upperPosition = valuePosition(upperBound, xAxisType);
  const valueAxisPosition = valuePosition(value, xAxisType);
  const span = upperPosition - lowerPosition;
  if (!Number.isFinite(span) || span <= 0 || !Number.isFinite(valueAxisPosition)) {
    return Number.NaN;
  }
  return Math.min(1, Math.max(0, (valueAxisPosition - lowerPosition) / span));
}

export function makeIntervalShapes(response, viewMode) {
  const shapes = [];
  const ciInterval = clippedVisibleInterval(response.summary.ci_display, response);
  if (hasCompatibilityPanel(viewMode) && ciInterval !== null) {
    shapes.push({
      type: "rect",
      xref: "x",
      yref: "y domain",
      x0: ciInterval[0],
      x1: ciInterval[1],
      y0: 0,
      y1: 1,
      fillcolor: INTERVAL_STYLES.ci.fillcolor,
      line: {
        color: INTERVAL_STYLES.ci.lineColor,
        width: 1,
      },
      layer: "below",
    });
  }

  const sMinus2 = response.meta.s_minus_2_interval;
  const sMinus2Interval = clippedVisibleInterval(sMinus2?.range_display, response);
  if (hasLikelihoodPanel(viewMode) && sMinus2 !== undefined) {
    const likelihoodAxis = viewMode === "both" ? "2" : "";
    const xref = likelihoodAxis === "2" ? "x2" : "x";
    const yref = likelihoodAxis === "2" ? "y2" : "y";
    const [visibleLower, visibleUpper] = visibleRange(response);
    if (sMinus2Interval !== null) {
      shapes.push({
        type: "rect",
        xref,
        yref: `${yref} domain`,
        x0: sMinus2Interval[0],
        x1: sMinus2Interval[1],
        y0: 0,
        y1: 1,
        fillcolor: INTERVAL_STYLES.sMinus2.fillcolor,
        line: {
          color: INTERVAL_STYLES.sMinus2.lineColor,
          width: 1,
        },
        layer: "below",
      });
    }
    if (Number.isFinite(visibleLower) && Number.isFinite(visibleUpper)) {
      shapes.push({
        type: "line",
        xref,
        yref,
        x0: visibleLower,
        x1: visibleUpper,
        y0: sMinus2.relative_likelihood_cutoff,
        y1: sMinus2.relative_likelihood_cutoff,
        line: {
          color: INTERVAL_STYLES.sMinus2.lineColor,
          dash: "dot",
          width: 1.5,
        },
        layer: "below",
      });
    }
  }

  return shapes;
}

export function makeIntervalAnnotations(response, viewMode, xAxisType, manuscript) {
  const annotations = [];
  const fontSize = manuscript ? 14 : 11;
  const ciInterval = clippedVisibleInterval(response.summary.ci_display, response);
  if (hasCompatibilityPanel(viewMode) && ciInterval !== null) {
    const x = normalizedXPosition(intervalMidpoint(ciInterval, xAxisType), response, xAxisType);
    if (Number.isFinite(x)) {
      annotations.push({
        x,
        y: viewMode === "both" ? 0.965 : 0.93,
        xref: "paper",
        yref: "paper",
        text: "Reported 95% CI",
        showarrow: false,
        xanchor: "center",
        yanchor: "top",
        font: {
          size: fontSize,
          color: INTERVAL_STYLES.ci.labelColor,
        },
        bgcolor: "rgba(255, 255, 255, 0.82)",
        bordercolor: "rgba(176, 74, 47, 0.22)",
        borderpad: 3,
      });
    }
  }

  const sMinus2 = response.meta.s_minus_2_interval;
  const sMinus2Interval = clippedVisibleInterval(sMinus2?.range_display, response);
  if (hasLikelihoodPanel(viewMode) && sMinus2 !== undefined && sMinus2Interval !== null) {
    const x = normalizedXPosition(
      intervalMidpoint(sMinus2Interval, xAxisType),
      response,
      xAxisType,
    );
    if (Number.isFinite(x)) {
      annotations.push({
        x,
        y: viewMode === "both" ? 0.15 : 0.22,
        xref: "paper",
        yref: "paper",
        text: "S−2 interval: within 7.4x of peak support",
        showarrow: false,
        xanchor: "center",
        yanchor: "bottom",
        font: {
          size: fontSize,
          color: INTERVAL_STYLES.sMinus2.labelColor,
        },
        bgcolor: "rgba(255, 255, 255, 0.84)",
        bordercolor: "rgba(19, 42, 58, 0.18)",
        borderpad: 3,
      });
    }
  }

  return annotations;
}

export function axisTitle(response) {
  const label = response.meta.effect_spec.label;
  return response.meta.effect_spec.family === "ratio" ? `${label} (natural scale)` : label;
}

export function axisType(response, displayOptions) {
  return response.meta.effect_spec.family === "ratio" && displayOptions.axisSpacing === "log"
    ? "log"
    : "linear";
}

function valuePosition(value, xAxisType) {
  if (xAxisType === "log") {
    return value > 0 ? Math.log10(value) : Number.NaN;
  }
  return value;
}

function visibleRange(response) {
  const values = response.grid.effect_display;
  return [values[0], values[values.length - 1]];
}

function shouldShowDirectLabel(marker, displayOptions, thresholdCount) {
  const isCompact = !displayOptions.manuscript && window.innerWidth < 700;
  if (!isCompact) {
    return true;
  }
  if (marker.key === "estimate" || marker.key === "null") {
    return true;
  }
  return marker.key === "threshold" && thresholdCount === 1;
}

export function makeDirectLabelAnnotations(response, displayOptions, xAxisType) {
  const [lowerBound, upperBound] = visibleRange(response);
  const lowerPosition = valuePosition(lowerBound, xAxisType);
  const upperPosition = valuePosition(upperBound, xAxisType);
  const span = upperPosition - lowerPosition;
  if (!Number.isFinite(span) || span <= 0) {
    return [];
  }

  const thresholdCount = response.meta.thresholds_display?.length ?? 0;
  const markers = makeReferenceMarkers(response)
    .filter((marker) => {
      if (!Number.isFinite(marker.value)) {
        return false;
      }
      if (marker.value < lowerBound || marker.value > upperBound) {
        return false;
      }
      return shouldShowDirectLabel(marker, displayOptions, thresholdCount);
    })
    .map((marker) => ({
      ...marker,
      position: valuePosition(marker.value, xAxisType),
    }))
    .filter((marker) => Number.isFinite(marker.position))
    .sort((left, right) => left.position - right.position);

  const fontSize = displayOptions.manuscript ? 15 : 12;
  const annotations = [];
  let previousPosition = Number.NEGATIVE_INFINITY;
  let staggerIndex = 0;
  const collisionDistance = span * 0.08;

  for (const marker of markers) {
    if (marker.position - previousPosition < collisionDistance) {
      staggerIndex = (staggerIndex + 1) % 3;
    } else {
      staggerIndex = 0;
    }
    previousPosition = marker.position;
    const normalizedPosition = (marker.position - lowerPosition) / span;
    const xAnchor =
      normalizedPosition < 0.08 ? "left" : normalizedPosition > 0.92 ? "right" : "center";

    annotations.push({
      x: Math.min(1, Math.max(0, normalizedPosition)),
      y: 1.015,
      xref: "paper",
      yref: "paper",
      text: marker.label,
      showarrow: false,
      xanchor: xAnchor,
      yanchor: "bottom",
      yshift: -18 * staggerIndex,
      font: {
        size: fontSize,
        color: REFERENCE_STYLES[marker.key].color,
      },
      bgcolor: "rgba(255, 255, 255, 0.86)",
      bordercolor: "rgba(19, 42, 58, 0.14)",
      borderpad: 3,
    });
  }

  return annotations;
}

export function makePanelAnnotations(viewMode, manuscript) {
  const font = {
    size: manuscript ? 16 : 13,
    color: "#132a3a",
  };
  if (viewMode === "likelihood") {
    return [
      {
        x: 0,
        y: 1.105,
        xref: "paper",
        yref: "paper",
        text: "B. Relative likelihood (normalized to 1 at the CI-implied estimate)",
        showarrow: false,
        xanchor: "left",
        yanchor: "bottom",
        font,
      },
    ];
  }
  if (viewMode === "compatibility") {
    return [
      {
        x: 0,
        y: 1.105,
        xref: "paper",
        yref: "paper",
        text: "A. Compatibility curve (two-sided Wald p-value function)",
        showarrow: false,
        xanchor: "left",
        yanchor: "bottom",
        font,
      },
    ];
  }
  return [
    {
      x: 0,
      y: 1.105,
      xref: "paper",
      yref: "paper",
      text: "A. Compatibility curve (two-sided Wald p-value function)",
      showarrow: false,
      xanchor: "left",
      yanchor: "bottom",
      font,
    },
    {
      x: 0,
      y: 0.435,
      xref: "paper",
      yref: "paper",
      text: "B. Relative likelihood (normalized to 1 at the CI-implied estimate)",
      showarrow: false,
      xanchor: "left",
      yanchor: "bottom",
      font,
    },
  ];
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

export function logAxisTickConfig(xValues) {
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

export function explicitAxisRange(response, xAxisType) {
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
