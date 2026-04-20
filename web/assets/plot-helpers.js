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
