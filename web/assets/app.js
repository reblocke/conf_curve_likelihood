import { DEFAULT_VALUES, DEFAULT_VIEW_MODE, EFFECT_OPTIONS } from "./config.js";
import { exportManuscriptPng, exportPlotPng, renderCurves } from "./plot.js";
import {
  buildCsv,
  buildFigureCaption,
  renderCommentary,
  renderComparisonHeader,
  renderPlotKey,
  renderSummary,
  renderWarnings,
} from "./renderers.js";
import { ensureRuntime } from "./runtime.js";

const pageShell = document.querySelector(".page-shell");
const sidebar = document.getElementById("controls-panel");
const toggleButton = document.getElementById("controls-toggle");
const desktopControlsToggle = document.getElementById("desktop-controls-toggle");
const form = document.getElementById("curve-form");
const statusCard = document.getElementById("status-card");
const summaryGrid = document.getElementById("summary-grid");
const commentaryText = document.getElementById("commentary-text");
const warningsList = document.getElementById("warnings-list");
const plotElement = document.getElementById("curve-plot");
const plotTitle = document.getElementById("plot-title");
const plotSubtitle = document.getElementById("plot-subtitle");
const comparisonTakeaway = document.getElementById("comparison-takeaway");
const figureCaption = document.getElementById("figure-caption");
const copyCaptionButton = document.getElementById("copy-caption");
const effectTypeSelect = document.getElementById("effect-type");
const estimateInput = document.getElementById("estimate");
const lowerInput = document.getElementById("ci-lower");
const upperInput = document.getElementById("ci-upper");
const nullInput = document.getElementById("null-value");
const thresholdsInput = document.getElementById("thresholds");
const axisSpacingGroup = document.getElementById("axis-spacing-group");
const axisSpacingSelect = document.getElementById("axis-spacing");
const displayRangeLowerInput = document.getElementById("display-range-lower");
const displayRangeUpperInput = document.getElementById("display-range-upper");
const gridPointsInput = document.getElementById("grid-points");
const gridPointsOutput = document.getElementById("grid-points-output");
const showCutoffsInput = document.getElementById("show-cutoffs");
const exportPngButton = document.getElementById("export-png");
const exportManuscriptPngButton = document.getElementById("export-manuscript-png");
const exportCsvButton = document.getElementById("export-csv");
const plotKey = document.getElementById("plot-key");
const viewModeInputs = Array.from(document.querySelectorAll("input[name='view_mode']"));

const comparisonHeaderElements = {
  plotTitle,
  plotSubtitle,
  comparisonTakeaway,
};

const runtimeState = {
  readyPromise: null,
  pyodide: null,
  computeCurvesJson: null,
  currentResponse: null,
  currentDisplayOptions: null,
  debounceId: null,
  lastDefaultNull: null,
};

function setStatus(state, message) {
  statusCard.dataset.state = state;
  statusCard.textContent = message;
}

function setExportEnabled(enabled) {
  exportCsvButton.disabled = !enabled;
  exportPngButton.disabled = !enabled;
  exportManuscriptPngButton.disabled = !enabled;
}

function clearRenderedState() {
  runtimeState.currentResponse = null;
  runtimeState.currentDisplayOptions = null;
  summaryGrid.innerHTML = "";
  commentaryText.textContent = "";
  warningsList.innerHTML = "";
  plotKey.innerHTML = "";
  comparisonTakeaway.textContent = "Enter a 95% confidence interval to compute the main comparison.";
  figureCaption.textContent = "";
  copyCaptionButton.disabled = true;
  if (typeof Plotly !== "undefined") {
    Plotly.purge(plotElement);
  }
  plotElement.innerHTML = "";
  setExportEnabled(false);
}

function parseOptionalNumber(rawValue) {
  const trimmed = rawValue.trim();
  if (trimmed === "") {
    return null;
  }
  const value = Number(trimmed);
  if (!Number.isFinite(value)) {
    throw new Error("Numeric inputs must be finite.");
  }
  return value;
}

function parseThresholds(rawValue) {
  if (rawValue.trim() === "") {
    return [];
  }
  return rawValue
    .split(/[,\s]+/)
    .filter(Boolean)
    .map((value) => {
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) {
        throw new Error("Thresholds must be comma-separated finite numbers.");
      }
      return parsed;
    });
}

function getSelectedEffect() {
  return EFFECT_OPTIONS.find((option) => option.key === effectTypeSelect.value) ?? EFFECT_OPTIONS[0];
}

function currentAxisSpacing() {
  return getSelectedEffect().family === "ratio" ? axisSpacingSelect.value : "linear";
}

function currentViewMode() {
  const selected = viewModeInputs.find((input) => input.checked);
  return selected?.value ?? DEFAULT_VIEW_MODE;
}

function currentDisplayOptions() {
  return {
    axisSpacing: currentAxisSpacing(),
    viewMode: currentViewMode(),
  };
}

function resizeCurrentPlot() {
  if (typeof Plotly === "undefined" || !plotElement._fullLayout) {
    return;
  }
  Plotly.Plots.resize(plotElement);
}

function schedulePlotResize() {
  window.requestAnimationFrame(() => {
    resizeCurrentPlot();
    window.setTimeout(resizeCurrentPlot, 220);
  });
}

function shouldReplaceWithDefaultNull(rawValue, previousDefaultNull) {
  const trimmed = rawValue.trim();
  if (trimmed === "") {
    return true;
  }
  if (previousDefaultNull === null) {
    return false;
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) && parsed === previousDefaultNull;
}

function updateEffectControls() {
  const effect = getSelectedEffect();
  if (shouldReplaceWithDefaultNull(nullInput.value, runtimeState.lastDefaultNull)) {
    nullInput.value = String(effect.defaultNull);
  }
  runtimeState.lastDefaultNull = effect.defaultNull;

  axisSpacingGroup.hidden = effect.family !== "ratio";
  axisSpacingSelect.disabled = effect.family !== "ratio";
  plotTitle.textContent = `How the data compare candidate ${effect.candidateLabel}`;
}

function buildPayload() {
  const effect = getSelectedEffect();
  return {
    effect_type: effect.key,
    estimate: parseOptionalNumber(estimateInput.value),
    lower: parseOptionalNumber(lowerInput.value),
    upper: parseOptionalNumber(upperInput.value),
    null_value: parseOptionalNumber(nullInput.value),
    thresholds: parseThresholds(thresholdsInput.value),
    display_range_lower: parseOptionalNumber(displayRangeLowerInput.value),
    display_range_upper: parseOptionalNumber(displayRangeUpperInput.value),
    display_natural_axis: effect.family === "ratio",
    grid_points: Number(gridPointsInput.value),
    show_cutoffs: showCutoffsInput.checked,
  };
}

async function renderResponse(response, displayOptions) {
  renderComparisonHeader(response, comparisonHeaderElements);
  renderSummary(response, summaryGrid);
  renderCommentary(response, displayOptions, commentaryText);
  renderWarnings(response, displayOptions, warningsList);
  renderPlotKey(response, displayOptions, plotKey);
  figureCaption.textContent = buildFigureCaption(response, displayOptions);
  copyCaptionButton.disabled = false;
  await renderCurves(plotElement, response, displayOptions);
  if (!plotElement.querySelector(".main-svg") || !plotElement._fullLayout) {
    throw new Error("Plot could not be rendered for the current inputs.");
  }
  runtimeState.currentResponse = response;
  runtimeState.currentDisplayOptions = displayOptions;
  setExportEnabled(true);
  setStatus("ready", "Curves updated.");
}

async function rerenderCurrentResponse() {
  if (!runtimeState.currentResponse) {
    scheduleCompute();
    return;
  }

  try {
    const displayOptions = currentDisplayOptions();
    await renderResponse(runtimeState.currentResponse, displayOptions);
  } catch (error) {
    clearRenderedState();
    const message = error instanceof Error ? error.message : String(error);
    setStatus("error", message);
  }
}

function downloadText(contents, filename, type) {
  const blob = new Blob([contents], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

async function computeAndRender() {
  let payload;
  try {
    payload = buildPayload();
  } catch (error) {
    clearRenderedState();
    setStatus("error", error.message);
    return;
  }

  if (payload.lower === null || payload.upper === null) {
    clearRenderedState();
    setStatus("loading", "Enter a 95% confidence interval to compute the curves.");
    return;
  }

  try {
    const displayOptions = currentDisplayOptions();
    await ensureRuntime(runtimeState, setStatus);
    setStatus("loading", "Computing Wald confidence and likelihood curves.");
    const resultJson = runtimeState.computeCurvesJson(JSON.stringify(payload));
    const response = JSON.parse(resultJson);

    await renderResponse(response, displayOptions);
  } catch (error) {
    clearRenderedState();
    const message = error instanceof Error ? error.message : String(error);
    setStatus("error", message);
  }
}

function scheduleCompute() {
  window.clearTimeout(runtimeState.debounceId);
  runtimeState.debounceId = window.setTimeout(() => {
    void computeAndRender();
  }, 150);
}

function initializeForm() {
  effectTypeSelect.innerHTML = EFFECT_OPTIONS.map(
    (option) => `<option value="${option.key}">${option.label}</option>`,
  ).join("");

  effectTypeSelect.value = DEFAULT_VALUES.effect_type;
  estimateInput.value = DEFAULT_VALUES.estimate;
  lowerInput.value = DEFAULT_VALUES.lower;
  upperInput.value = DEFAULT_VALUES.upper;
  nullInput.value = DEFAULT_VALUES.null_value;
  thresholdsInput.value = DEFAULT_VALUES.thresholds;
  displayRangeLowerInput.value = DEFAULT_VALUES.display_range_lower;
  displayRangeUpperInput.value = DEFAULT_VALUES.display_range_upper;
  axisSpacingSelect.value = DEFAULT_VALUES.axis_spacing;
  for (const input of viewModeInputs) {
    input.checked = input.value === DEFAULT_VIEW_MODE;
  }
  gridPointsInput.value = DEFAULT_VALUES.grid_points;
  gridPointsOutput.value = DEFAULT_VALUES.grid_points;
  gridPointsOutput.textContent = DEFAULT_VALUES.grid_points;
  showCutoffsInput.checked = DEFAULT_VALUES.show_cutoffs;
  runtimeState.lastDefaultNull = getSelectedEffect().defaultNull;

  updateEffectControls();
}

function initializeUi() {
  pageShell.dataset.controlsCollapsed = "false";
  sidebar.dataset.collapsed = "false";
  setExportEnabled(false);
  copyCaptionButton.disabled = true;
  toggleButton.addEventListener("click", () => {
    const nextCollapsed = sidebar.dataset.collapsed !== "true";
    sidebar.dataset.collapsed = nextCollapsed ? "true" : "false";
    toggleButton.setAttribute("aria-expanded", String(!nextCollapsed));
  });
  desktopControlsToggle.addEventListener("click", () => {
    const nextCollapsed = pageShell.dataset.controlsCollapsed !== "true";
    pageShell.dataset.controlsCollapsed = nextCollapsed ? "true" : "false";
    desktopControlsToggle.setAttribute("aria-pressed", String(nextCollapsed));
    desktopControlsToggle.textContent = nextCollapsed ? "Show controls" : "Hide controls";
    schedulePlotResize();
  });

  if (typeof ResizeObserver !== "undefined") {
    let resizeFrame = null;
    const resizeObserver = new ResizeObserver(() => {
      if (resizeFrame !== null) {
        window.cancelAnimationFrame(resizeFrame);
      }
      resizeFrame = window.requestAnimationFrame(() => {
        resizeFrame = null;
        resizeCurrentPlot();
      });
    });
    resizeObserver.observe(plotElement);
  }

  gridPointsInput.addEventListener("input", (event) => {
    const nextValue = event.target.value;
    gridPointsOutput.value = nextValue;
    gridPointsOutput.textContent = nextValue;
    scheduleCompute();
  });

  effectTypeSelect.addEventListener("change", () => {
    updateEffectControls();
    scheduleCompute();
  });

  for (const input of viewModeInputs) {
    input.addEventListener("change", () => {
      void rerenderCurrentResponse();
    });
  }

  form.addEventListener("input", (event) => {
    if (event.target !== gridPointsInput) {
      scheduleCompute();
    }
  });
  form.addEventListener("change", scheduleCompute);

  exportCsvButton.addEventListener("click", () => {
    if (!runtimeState.currentResponse) {
      return;
    }
    downloadText(
      buildCsv(runtimeState.currentResponse),
      "wald-confidence-curves.csv",
      "text/csv;charset=utf-8",
    );
  });

  exportPngButton.addEventListener("click", async () => {
    if (!runtimeState.currentResponse) {
      return;
    }
    await exportPlotPng(plotElement, "wald-confidence-curves.png");
  });

  exportManuscriptPngButton.addEventListener("click", async () => {
    if (!runtimeState.currentResponse || !runtimeState.currentDisplayOptions) {
      return;
    }
    await exportManuscriptPng(
      runtimeState.currentResponse,
      runtimeState.currentDisplayOptions,
      "wald-confidence-curves-manuscript.png",
    );
  });

  copyCaptionButton.addEventListener("click", async () => {
    const captionText = figureCaption.textContent.trim();
    if (!captionText) {
      return;
    }
    const originalText = copyCaptionButton.textContent;
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(captionText);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = captionText;
        document.body.append(textArea);
        textArea.select();
        document.execCommand("copy");
        textArea.remove();
      }
      copyCaptionButton.textContent = "Copied";
      window.setTimeout(() => {
        copyCaptionButton.textContent = originalText;
      }, 1400);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setStatus("error", `Could not copy caption: ${message}`);
    }
  });
}

initializeForm();
initializeUi();
setStatus("loading", "Preparing browser runtime and first render.");
scheduleCompute();
