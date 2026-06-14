import {
  DEFAULT_DESIGN_METRIC,
  DEFAULT_VALUES,
  DEFAULT_VIEW_MODE,
  DESIGN_METRIC_OPTIONS,
  DESIGN_SELECTION_RULE_OPTIONS,
  EFFECT_OPTIONS,
} from "./config.js";
import { exportManuscriptPng, exportPlotPng, renderCurves } from "./plot.js";
import {
  buildCsv,
  buildFigureCaption,
  renderCommentary,
  renderComparisonHeader,
  renderDesignResults,
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
const designEnabledInput = document.getElementById("design-enabled");
const designFields = document.getElementById("design-fields");
const designAlphaInput = document.getElementById("design-alpha");
const designSelectionRuleSelect = document.getElementById("design-selection-rule");
const designClaimDirectionGroup = document.getElementById("design-claim-direction-group");
const designClaimDirectionSelect = document.getElementById("design-claim-direction");
const designClaimThresholdGroup = document.getElementById("design-claim-threshold-group");
const designClaimThresholdInput = document.getElementById("design-claim-threshold");
const designInformationMultiplierInput = document.getElementById("design-information-multiplier");
const designTrueEffectsInput = document.getElementById("design-true-effects");
const designRangeLowerInput = document.getElementById("design-range-lower");
const designRangeUpperInput = document.getElementById("design-range-upper");
const designPrecisionTargetSelect = document.getElementById("design-precision-target-effect");
const designTargetPowerInput = document.getElementById("design-target-power");
const designMaxTypeSInput = document.getElementById("design-max-type-s");
const designMaxTypeMInput = document.getElementById("design-max-type-m");
const designMetricSelect = document.getElementById("design-metric");
const designResults = document.getElementById("design-results");
const designSummary = document.getElementById("design-summary");
const designScenarioTable = document.getElementById("design-scenario-table");
const designPrecisionTargetTable = document.getElementById("design-precision-target-table");
const reviewerScenarioSelect = document.getElementById("reviewer-scenario");
const reviewerText = document.getElementById("reviewer-text");
const copyReviewerTextButton = document.getElementById("copy-reviewer-text");
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

const designResultElements = {
  container: designResults,
  summary: designSummary,
  scenarioTable: designScenarioTable,
  precisionTargetTable: designPrecisionTargetTable,
  reviewerScenarioSelect,
  reviewerText,
  copyReviewerTextButton,
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
  designResults.hidden = true;
  designSummary.textContent = "";
  designScenarioTable.innerHTML = "";
  designPrecisionTargetTable.innerHTML = "";
  reviewerScenarioSelect.innerHTML = "";
  reviewerText.textContent = "";
  copyReviewerTextButton.disabled = true;
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

function parseNumberList(rawValue, errorMessage) {
  if (rawValue.trim() === "") {
    return [];
  }
  return rawValue
    .split(/[,\s]+/)
    .filter(Boolean)
    .map((value) => {
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) {
        throw new Error(errorMessage);
      }
      return parsed;
    });
}

function safeParseNumberList(rawValue) {
  try {
    return parseNumberList(rawValue, "Values must be comma-separated finite numbers.");
  } catch {
    return [];
  }
}

function designSelectionRuleOption() {
  return (
    DESIGN_SELECTION_RULE_OPTIONS.find((option) => option.key === designSelectionRuleSelect.value) ??
    DESIGN_SELECTION_RULE_OPTIONS[0]
  );
}

function deduplicateTargetCandidates(candidates) {
  const deduplicated = [];
  for (const candidate of candidates) {
    const alreadySeen = deduplicated.some(
      (existing) =>
        Math.abs(existing.value - candidate.value) <=
        Math.max(1e-12, Math.abs(candidate.value) * 1e-10),
    );
    if (!alreadySeen) {
      deduplicated.push(candidate);
    }
  }
  return deduplicated;
}

function refreshPrecisionTargetOptions() {
  const previousValue = designPrecisionTargetSelect.value;
  const candidates = deduplicateTargetCandidates([
    ...safeParseNumberList(thresholdsInput.value).map((value) => ({
      label: `Threshold / MCID: ${value}`,
      value,
    })),
    ...safeParseNumberList(designTrueEffectsInput.value).map((value) => ({
      label: `Assumed true effect: ${value}`,
      value,
    })),
  ]);

  const emptyLabel =
    candidates.length === 0 ? "Add a threshold or assumed true effect" : "No precision target";
  designPrecisionTargetSelect.innerHTML = [
    `<option value="">${emptyLabel}</option>`,
    ...candidates.map((candidate) => `<option value="${candidate.value}">${candidate.label}</option>`),
  ].join("");
  if (candidates.some((candidate) => String(candidate.value) === previousValue)) {
    designPrecisionTargetSelect.value = previousValue;
  } else {
    designPrecisionTargetSelect.value = "";
  }
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
    designMetric: designMetricSelect.value || DEFAULT_DESIGN_METRIC,
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

function updateDesignControls() {
  const enabled = designEnabledInput.checked;
  const ruleOption = designSelectionRuleOption();

  refreshPrecisionTargetOptions();
  const hasPrecisionTarget = designPrecisionTargetSelect.value !== "";
  designFields.hidden = !enabled;
  designClaimDirectionGroup.hidden = !ruleOption.usesDirection;
  designClaimThresholdGroup.hidden = !ruleOption.usesThreshold;
  for (const input of designFields.querySelectorAll("input, select")) {
    input.disabled = !enabled;
  }
  if (!enabled || !ruleOption.usesDirection) {
    designClaimDirectionSelect.disabled = true;
  }
  if (!enabled || !ruleOption.usesThreshold) {
    designClaimThresholdInput.disabled = true;
  }
  for (const input of [designTargetPowerInput, designMaxTypeSInput, designMaxTypeMInput]) {
    input.disabled = !enabled || !hasPrecisionTarget;
  }
}

function buildPayload() {
  const effect = getSelectedEffect();
  const designEnabled = designEnabledInput.checked;
  const designAlpha = parseOptionalNumber(designAlphaInput.value);
  const designSelectionRule = designSelectionRuleSelect.value;
  const designRuleOption = designSelectionRuleOption();
  const designClaimThreshold = parseOptionalNumber(designClaimThresholdInput.value);
  const designInformationMultiplier = parseOptionalNumber(designInformationMultiplierInput.value);
  const designRangeLower = parseOptionalNumber(designRangeLowerInput.value);
  const designRangeUpper = parseOptionalNumber(designRangeUpperInput.value);
  const designPrecisionTargetEffect = parseOptionalNumber(designPrecisionTargetSelect.value);
  const designTargetPower = parseOptionalNumber(designTargetPowerInput.value);
  const designMaxTypeS = parseOptionalNumber(designMaxTypeSInput.value);
  const designMaxTypeM = parseOptionalNumber(designMaxTypeMInput.value);
  if (designEnabled && (designAlpha === null || designAlpha <= 0 || designAlpha >= 1)) {
    throw new Error("Selection threshold alpha must be greater than 0 and less than 1.");
  }
  if (
    designEnabled &&
    (designInformationMultiplier === null || designInformationMultiplier <= 0)
  ) {
    throw new Error("Design information multiplier must be greater than 0.");
  }
  if (designEnabled && designRuleOption.usesThreshold && designClaimThreshold === null) {
    throw new Error("This selection rule requires a finite claim threshold / MCID.");
  }
  if (designEnabled && (designRangeLower === null) !== (designRangeUpper === null)) {
    throw new Error("Design plausible true-effect range lower and upper must be supplied together.");
  }
  if (designEnabled && designPrecisionTargetEffect !== null) {
    if (designTargetPower !== null && (designTargetPower <= 0 || designTargetPower >= 1)) {
      throw new Error("Target power must be greater than 0 and less than 1.");
    }
    if (designMaxTypeS !== null && (designMaxTypeS <= 0 || designMaxTypeS >= 1)) {
      throw new Error("Maximum Type S must be greater than 0 and less than 1.");
    }
    if (designMaxTypeM !== null && designMaxTypeM <= 1) {
      throw new Error("Maximum Type M must be greater than 1.");
    }
  }

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
    design_enabled: designEnabled,
    design_alpha: designAlpha ?? Number(DEFAULT_VALUES.design_alpha),
    design_selection_rule: designEnabled ? designSelectionRule : DEFAULT_VALUES.design_selection_rule,
    design_claim_direction: designEnabled
      ? designClaimDirectionSelect.value
      : DEFAULT_VALUES.design_claim_direction,
    design_claim_threshold:
      designEnabled && designRuleOption.usesThreshold ? designClaimThreshold : null,
    design_information_multiplier: designEnabled
      ? designInformationMultiplier
      : Number(DEFAULT_VALUES.design_information_multiplier),
    design_precision_target_effect: designEnabled ? designPrecisionTargetEffect : null,
    design_target_power:
      designEnabled && designPrecisionTargetEffect !== null ? designTargetPower : null,
    design_max_type_s:
      designEnabled && designPrecisionTargetEffect !== null ? designMaxTypeS : null,
    design_max_type_m:
      designEnabled && designPrecisionTargetEffect !== null ? designMaxTypeM : null,
    design_true_effects: designEnabled
      ? parseNumberList(
          designTrueEffectsInput.value,
          "Assumed true effects must be comma-separated finite numbers.",
        )
      : [],
    design_plausible_range_lower: designEnabled ? designRangeLower : null,
    design_plausible_range_upper: designEnabled ? designRangeUpper : null,
  };
}

async function renderResponse(response, displayOptions) {
  renderComparisonHeader(response, comparisonHeaderElements);
  renderSummary(response, summaryGrid);
  renderCommentary(response, displayOptions, commentaryText);
  renderWarnings(response, displayOptions, warningsList);
  renderPlotKey(response, displayOptions, plotKey);
  renderDesignResults(response, designResultElements);
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
  designEnabledInput.checked = DEFAULT_VALUES.design_enabled;
  designAlphaInput.value = DEFAULT_VALUES.design_alpha;
  designSelectionRuleSelect.innerHTML = DESIGN_SELECTION_RULE_OPTIONS.map(
    (option) => `<option value="${option.key}">${option.label}</option>`,
  ).join("");
  designSelectionRuleSelect.value = DEFAULT_VALUES.design_selection_rule;
  designClaimDirectionSelect.value = DEFAULT_VALUES.design_claim_direction;
  designClaimThresholdInput.value = DEFAULT_VALUES.design_claim_threshold;
  designInformationMultiplierInput.value = DEFAULT_VALUES.design_information_multiplier;
  designTrueEffectsInput.value = DEFAULT_VALUES.design_true_effects;
  designRangeLowerInput.value = DEFAULT_VALUES.design_plausible_range_lower;
  designRangeUpperInput.value = DEFAULT_VALUES.design_plausible_range_upper;
  designTargetPowerInput.value = DEFAULT_VALUES.design_target_power;
  designMaxTypeSInput.value = DEFAULT_VALUES.design_max_type_s;
  designMaxTypeMInput.value = DEFAULT_VALUES.design_max_type_m;
  refreshPrecisionTargetOptions();
  designPrecisionTargetSelect.value = DEFAULT_VALUES.design_precision_target_effect;
  designMetricSelect.innerHTML = DESIGN_METRIC_OPTIONS.map(
    (option) => `<option value="${option.key}">${option.label}</option>`,
  ).join("");
  designMetricSelect.value = DEFAULT_VALUES.design_metric;
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
  updateDesignControls();
}

function initializeUi() {
  pageShell.dataset.controlsCollapsed = "false";
  sidebar.dataset.collapsed = "false";
  setExportEnabled(false);
  copyCaptionButton.disabled = true;
  copyReviewerTextButton.disabled = true;
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
  designEnabledInput.addEventListener("change", () => {
    updateDesignControls();
    scheduleCompute();
  });
  designSelectionRuleSelect.addEventListener("change", () => {
    updateDesignControls();
    scheduleCompute();
  });
  designPrecisionTargetSelect.addEventListener("change", () => {
    updateDesignControls();
    scheduleCompute();
  });
  for (const input of [thresholdsInput, designTrueEffectsInput]) {
    input.addEventListener("input", () => {
      updateDesignControls();
    });
  }
  designMetricSelect.addEventListener("change", () => {
    void rerenderCurrentResponse();
  });
  reviewerScenarioSelect.addEventListener("change", () => {
    if (runtimeState.currentResponse) {
      renderDesignResults(runtimeState.currentResponse, designResultElements);
    }
  });

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

  copyReviewerTextButton.addEventListener("click", async () => {
    const text = reviewerText.textContent.trim();
    if (!text) {
      return;
    }
    const originalText = copyReviewerTextButton.textContent;
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(text);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        document.body.append(textArea);
        textArea.select();
        document.execCommand("copy");
        textArea.remove();
      }
      copyReviewerTextButton.textContent = "Copied";
      window.setTimeout(() => {
        copyReviewerTextButton.textContent = originalText;
      }, 1400);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setStatus("error", `Could not copy reviewer text: ${message}`);
    }
  });
}

initializeForm();
initializeUi();
setStatus("loading", "Preparing browser runtime and first render.");
scheduleCompute();
