import { exportManuscriptPng, exportPlotPng, renderCurves } from "./plot.js";

const PYODIDE_VERSION = "0.29.3";
const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYTHON_PACKAGE_FILES = ["__init__.py", "core.py", "models.py", "stage.py", "web_contract.py"];
const DEFAULT_VIEW_MODE = "both";
const EFFECT_OPTIONS = [
  {
    key: "odds_ratio",
    label: "Odds ratio",
    shortLabel: "OR",
    candidateLabel: "odds ratios",
    family: "ratio",
    defaultNull: 1,
  },
  {
    key: "risk_ratio",
    label: "Risk ratio",
    shortLabel: "RR",
    candidateLabel: "risk ratios",
    family: "ratio",
    defaultNull: 1,
  },
  {
    key: "hazard_ratio",
    label: "Hazard ratio",
    shortLabel: "HR",
    candidateLabel: "hazard ratios",
    family: "ratio",
    defaultNull: 1,
  },
  {
    key: "incidence_rate_ratio",
    label: "Incidence rate ratio",
    shortLabel: "IRR",
    candidateLabel: "incidence rate ratios",
    family: "ratio",
    defaultNull: 1,
  },
  {
    key: "ratio_of_means",
    label: "Ratio of means",
    shortLabel: "ratio",
    candidateLabel: "ratios of means",
    family: "ratio",
    defaultNull: 1,
  },
  {
    key: "mean_difference",
    label: "Mean difference",
    shortLabel: "mean difference",
    candidateLabel: "mean differences",
    family: "additive",
    defaultNull: 0,
  },
  {
    key: "risk_difference",
    label: "Risk difference",
    shortLabel: "risk difference",
    candidateLabel: "risk differences",
    family: "additive",
    defaultNull: 0,
  },
  {
    key: "rate_difference",
    label: "Rate difference",
    shortLabel: "rate difference",
    candidateLabel: "rate differences",
    family: "additive",
    defaultNull: 0,
  },
  {
    key: "regression_coefficient",
    label: "Regression coefficient",
    shortLabel: "coefficient",
    candidateLabel: "regression coefficients",
    family: "additive",
    defaultNull: 0,
  },
];
const DEFAULT_VALUES = {
  effect_type: "odds_ratio",
  estimate: "",
  lower: "1.2",
  upper: "2.7",
  null_value: "1",
  thresholds: "",
  display_range_lower: "",
  display_range_upper: "",
  axis_spacing: "log",
  grid_points: "801",
  show_cutoffs: true,
};

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

function formatNumber(value) {
  if (!Number.isFinite(value)) {
    return String(value);
  }
  const magnitude = Math.abs(value);
  if (magnitude >= 1_000 || (magnitude > 0 && magnitude < 0.001)) {
    return value.toExponential(3);
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 4,
  }).format(value);
}

function formatLikelihoodRatio(summary) {
  if (summary.likelihood_ratio_mle_to_null !== null) {
    return formatNumber(summary.likelihood_ratio_mle_to_null);
  }
  if (summary.log_likelihood_ratio_mle_to_null === null) {
    return "Overflow";
  }
  const log10LikelihoodRatio = summary.log_likelihood_ratio_mle_to_null / Math.LN10;
  return `Overflow (log10 LR ${formatNumber(log10LikelihoodRatio)})`;
}

function formatOptionalLikelihoodRatio(value, logValue) {
  if (value !== null) {
    return `${formatNumber(value)}x`;
  }
  if (logValue === null) {
    return "not finite";
  }
  const log10LikelihoodRatio = logValue / Math.LN10;
  return `log10 ratio ${formatNumber(log10LikelihoodRatio)}`;
}

function formatRange(values) {
  if (!Array.isArray(values) || values.length !== 2) {
    return "";
  }
  return `${formatNumber(values[0])} to ${formatNumber(values[1])}`;
}

function effectOptionForResponse(response) {
  return (
    EFFECT_OPTIONS.find((option) => option.key === response.meta.effect_spec.key) ??
    getSelectedEffect()
  );
}

function estimateSourceLabel(estimateSource) {
  return estimateSource === "provided_validated"
    ? "Provided and validated"
    : "CI-implied from 95% CI";
}

function effectValueLabel(effect, value) {
  return `${effect.shortLabel} = ${formatNumber(value)}`;
}

function supportPhrase(relativeLikelihood) {
  if (relativeLikelihood >= 0.5) {
    return "substantial support";
  }
  if (relativeLikelihood >= 0.1) {
    return "moderate support";
  }
  if (relativeLikelihood >= 0.01) {
    return "limited support";
  }
  return "very weak support";
}

function thresholdVsNullPhrase(thresholdSummary) {
  const value = thresholdSummary.likelihood_ratio_threshold_to_null;
  const logValue = thresholdSummary.log_likelihood_ratio_threshold_to_null;
  if (value === null && logValue === null) {
    return "cannot be compared with the null using finite likelihood values";
  }
  if (value === null) {
    return `has more support than the null (${formatOptionalLikelihoodRatio(value, logValue)})`;
  }
  if (value >= 1) {
    return `is ${formatNumber(value)}x as supported as the null`;
  }
  return `has ${formatNumber(value)}x the null support`;
}

function buildComparisonTakeaway(response) {
  const effect = effectOptionForResponse(response);
  const estimateLabel = effectValueLabel(effect, response.summary.estimate_display);
  const nullLabel = effectValueLabel(effect, response.summary.null_display);
  const nullSupport = supportPhrase(response.summary.null_relative_likelihood);
  const thresholdSummaries = response.meta.threshold_support_summaries ?? [];

  let takeaway = `Peak support is at ${estimateLabel}; the null ${nullLabel} has ${nullSupport} (relative likelihood ${formatNumber(response.summary.null_relative_likelihood)}).`;

  if (thresholdSummaries.length > 0) {
    const thresholdSummary = thresholdSummaries[0];
    takeaway += ` The clinical threshold ${effectValueLabel(effect, thresholdSummary.threshold_display)} ${thresholdVsNullPhrase(thresholdSummary)}.`;
  } else {
    takeaway += ` The CI-implied estimate is ${formatLikelihoodRatio(response.summary)}x as supported as the null under this reconstruction.`;
  }

  return takeaway;
}

function renderComparisonHeader(response) {
  const effect = effectOptionForResponse(response);
  const hasThresholds = (response.meta.threshold_support_summaries ?? []).length > 0;

  plotTitle.textContent = `How the data compare candidate ${effect.candidateLabel}`;
  plotSubtitle.textContent = hasThresholds
    ? `Relative to the null ${effect.shortLabel} = ${formatNumber(response.summary.null_display)} and clinical thresholds`
    : "Relative to the null and the CI-implied estimate";
  comparisonTakeaway.textContent = buildComparisonTakeaway(response);
}

function buildFigureCaption(response, displayOptions) {
  const effect = effectOptionForResponse(response);
  const panelText =
    displayOptions.viewMode === "likelihood"
      ? "The figure shows relative likelihood only."
      : displayOptions.viewMode === "compatibility"
        ? "The figure shows the compatibility curve only."
        : "Panel A shows the compatibility curve and Panel B shows relative likelihood.";
  const thresholdValues = response.meta.thresholds_display ?? [];
  const thresholdText =
    thresholdValues.length > 0
      ? ` Clinical thresholds are marked at ${thresholdValues.map(formatNumber).join(", ")}.`
      : "";

  return (
    `Figure. Wald reconstruction from the reported 95% CI (${formatRange(response.summary.ci_display)}) for ${effect.label.toLowerCase()}. ` +
    `The CI-implied point estimate is ${effectValueLabel(effect, response.summary.estimate_display)} and the null is ${effectValueLabel(effect, response.summary.null_display)}. ` +
    `${panelText} Relative likelihood is normalized to 1 at the CI-implied estimate; compatibility is the two-sided Wald p-value function across candidate effect sizes.` +
    `${thresholdText} This is not exact fitted-model profile likelihood.`
  );
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

function hasCompatibilityPanel(viewMode) {
  return viewMode !== "likelihood";
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

async function installLocalPythonPackage(pyodide) {
  pyodide.FS.mkdirTree("/home/pyodide/confcurve");

  for (const fileName of PYTHON_PACKAGE_FILES) {
    const response = await fetch(`./assets/py/confcurve/${fileName}`);
    if (!response.ok) {
      throw new Error(`Failed to load staged Python file: ${fileName}`);
    }
    const source = await response.text();
    pyodide.FS.writeFile(`/home/pyodide/confcurve/${fileName}`, source);
  }

  await pyodide.runPythonAsync(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
`);
}

async function ensureRuntime() {
  if (runtimeState.readyPromise) {
    return runtimeState.readyPromise;
  }

  runtimeState.readyPromise = (async () => {
    setStatus("loading", "Loading Pyodide, NumPy, and SciPy in the browser.");
    const pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX_URL });
    await pyodide.loadPackage(["numpy", "scipy"]);
    await installLocalPythonPackage(pyodide);
    await pyodide.runPythonAsync(`
import json
from confcurve import compute_curves

def compute_curves_json(payload_json):
    return json.dumps(compute_curves(json.loads(payload_json)))
`);
    runtimeState.pyodide = pyodide;
    runtimeState.computeCurvesJson = pyodide.globals.get("compute_curves_json");
    setStatus("ready", "Scientific runtime ready.");
    return runtimeState;
  })();

  return runtimeState.readyPromise;
}

function renderSummary(response) {
  const thresholdRows = (response.meta.threshold_support_summaries ?? []).map((thresholdSummary) => [
    `Threshold ${formatNumber(thresholdSummary.threshold_display)} support`,
    `${formatNumber(thresholdSummary.relative_likelihood)} relative; ${thresholdVsNullPhrase(thresholdSummary)}`,
  ]);
  const technicalItems = [
    ["Estimate source", estimateSourceLabel(response.meta.estimate_source)],
    ["Working-scale SE", response.summary.working_scale_se],
    [
      "Computation scale",
      response.meta.effect_spec.working_scale === "log" ? "Log working scale" : "Natural working scale",
    ],
    ["Design threshold markers", formatRange(response.summary.critical_effect_markers_display)],
  ];
  if (response.meta.display_range_active && response.meta.display_range_display) {
    technicalItems.push(["Display range", formatRange(response.meta.display_range_display)]);
  }

  const groups = [
    {
      title: "Main comparison",
      items: [
        ["Point Estimate", response.summary.estimate_display],
        [
          "95% CI",
          `${formatNumber(response.summary.ci_display[0])} to ${formatNumber(response.summary.ci_display[1])}`,
        ],
        ["Null relative likelihood", response.summary.null_relative_likelihood],
        ["MLE:null likelihood ratio", formatLikelihoodRatio(response.summary)],
        ["Two-sided Wald p-value", response.summary.two_sided_wald_p_value],
        ...thresholdRows,
      ],
    },
    {
      title: "Technical reconstruction",
      items: technicalItems,
    },
  ];

  summaryGrid.innerHTML = groups
    .map(
      (group) => `
      <section class="summary-group">
        <h3 class="summary-group-title">${group.title}</h3>
        <div class="summary-items">
          ${group.items
            .map(
              ([label, value]) => `
        <div class="summary-item">
          <span class="summary-label">${label}</span>
          <span class="summary-value">${typeof value === "number" ? formatNumber(value) : value}</span>
        </div>
      `,
            )
            .join("")}
        </div>
      </section>
      `,
    )
    .join("");
}

function renderPlotKey(response, displayOptions) {
  const keyRows = [
    ["estimate", "Point estimate"],
    ["null", "Null value"],
    ["critical", "Design threshold markers"],
  ];
  if (response.meta.thresholds_display.length > 0) {
    keyRows.push(["threshold", "Clinical thresholds"]);
  }
  if (response.meta.show_cutoffs && hasCompatibilityPanel(displayOptions.viewMode)) {
    keyRows.push(["cutoff", "Compatibility cutoffs"]);
  }

  plotKey.innerHTML = keyRows
    .map(
      ([key, label]) => `
        <span class="key-item">
          <span class="key-line key-line-${key}" aria-hidden="true"></span>
          <span>${label}</span>
        </span>
      `,
    )
    .join("");
}

function renderCommentary(response, displayOptions) {
  const nullValue = formatNumber(response.summary.null_display);
  const estimateClause =
    response.meta.estimate_source === "provided_validated"
      ? "The supplied point estimate matched the 95% CI within rounding tolerance, and the plotted estimate uses the CI-implied midpoint on the working scale."
      : "No point estimate was supplied, so the plotted estimate is the CI-implied midpoint of the 95% CI on the working scale.";
  const spacingClause =
    response.meta.effect_spec.family === "ratio"
      ? `The ratio axis is labeled on the natural scale and uses ${displayOptions.axisSpacing} spacing.`
      : "The additive axis is displayed on its natural linear scale.";
  const likelihoodRatioClause =
    response.summary.likelihood_ratio_mle_to_null === null
      ? `Because the null value is ${nullValue}, the implied MLE:null likelihood ratio exceeds browser floating-point range.`
      : `Because the null value is ${nullValue}, the observed data are ${formatLikelihoodRatio(response.summary)} times as compatible with the CI-implied estimate as with the null.`;
  const viewClause =
    displayOptions.viewMode === "likelihood"
      ? "The visible panel foregrounds relative evidentiary support: values nearer 1 are better supported under the Wald approximation, and lower values have less support relative to the CI-implied estimate."
      : displayOptions.viewMode === "compatibility"
        ? "The visible panel is the compatibility / confidence curve: a two-sided Wald p-value function evaluated across candidate effect sizes."
        : "The two panels summarize the same Wald approximation in different units: the compatibility / confidence curve is a two-sided p-value function, and the relative likelihood curve is a monotone transform of the same Wald distance.";
  commentaryText.textContent =
    `${viewClause} ` +
    `${estimateClause} ` +
    `${spacingClause} ` +
    `The paired design threshold markers show the alpha=0.05, power=0.80 distance around the null. ` +
    `${likelihoodRatioClause} ` +
    `This display is reconstructed from the confidence interval; it is not the exact fitted-model profile likelihood from the original study.`;
}

function renderWarnings(response, displayOptions) {
  const notes = [
    response.meta.effect_spec.family === "ratio"
      ? `Computations are performed on the log scale and displayed with natural-scale labels using ${displayOptions.axisSpacing} spacing.`
      : "Computations are performed on the natural additive working scale.",
    `Standard error reconstruction method: ${response.meta.se_method}.`,
  ];
  if (response.meta.thresholds_display.length > 0) {
    notes.push("Clinical thresholds are shown as dashed green vertical reference lines.");
  }
  if (response.meta.display_range_active && response.meta.display_range_display) {
    notes.push(
      `Plausible display range is active from ${formatRange(response.meta.display_range_display)}; summaries still use the original CI-derived reconstruction.`,
    );
  }
  if (response.meta.show_cutoffs && hasCompatibilityPanel(displayOptions.viewMode)) {
    const cutoffPanel =
      displayOptions.viewMode === "both" ? "upper compatibility panel" : "compatibility panel";
    notes.push(
      `Horizontal guide lines on the ${cutoffPanel} mark 90%, 95%, and 99% compatibility cutoffs.`,
    );
  }
  const messages = [...notes, ...response.warnings];

  warningsList.innerHTML = messages.map((message) => `<li>${message}</li>`).join("");
}

async function renderResponse(response, displayOptions) {
  renderComparisonHeader(response);
  renderSummary(response);
  renderCommentary(response, displayOptions);
  renderWarnings(response, displayOptions);
  renderPlotKey(response, displayOptions);
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

function csvValue(value) {
  if (Number.isFinite(value)) {
    return String(value);
  }
  return `"${String(value)}"`;
}

function buildCsv(response) {
  const headers = [
    "effect_display",
    "effect_working",
    "z",
    "compatibility",
    "relative_likelihood",
    "log_relative_likelihood",
  ];
  const rows = [headers.join(",")];

  for (let index = 0; index < response.grid.effect_display.length; index += 1) {
    rows.push(
      headers
        .map((header) => csvValue(response.grid[header][index]))
        .join(","),
    );
  }

  return `${rows.join("\n")}\n`;
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
    await ensureRuntime();
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
