import { exportPlotPng, renderCurves } from "./plot.js";

const PYODIDE_VERSION = "0.29.3";
const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYTHON_PACKAGE_FILES = ["__init__.py", "core.py", "models.py", "stage.py", "web_contract.py"];
const EFFECT_OPTIONS = [
  { key: "odds_ratio", label: "Odds ratio", family: "ratio", defaultNull: 1 },
  { key: "risk_ratio", label: "Risk ratio", family: "ratio", defaultNull: 1 },
  { key: "hazard_ratio", label: "Hazard ratio", family: "ratio", defaultNull: 1 },
  { key: "incidence_rate_ratio", label: "Incidence rate ratio", family: "ratio", defaultNull: 1 },
  { key: "ratio_of_means", label: "Ratio of means", family: "ratio", defaultNull: 1 },
  { key: "mean_difference", label: "Mean difference", family: "additive", defaultNull: 0 },
  { key: "risk_difference", label: "Risk difference", family: "additive", defaultNull: 0 },
  { key: "rate_difference", label: "Rate difference", family: "additive", defaultNull: 0 },
  {
    key: "regression_coefficient",
    label: "Regression coefficient",
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
  display_natural_axis: true,
  grid_points: "801",
  show_cutoffs: true,
};

const sidebar = document.getElementById("controls-panel");
const toggleButton = document.getElementById("controls-toggle");
const form = document.getElementById("curve-form");
const statusCard = document.getElementById("status-card");
const summaryGrid = document.getElementById("summary-grid");
const commentaryText = document.getElementById("commentary-text");
const warningsList = document.getElementById("warnings-list");
const plotElement = document.getElementById("curve-plot");
const effectTypeSelect = document.getElementById("effect-type");
const estimateInput = document.getElementById("estimate");
const lowerInput = document.getElementById("ci-lower");
const upperInput = document.getElementById("ci-upper");
const nullInput = document.getElementById("null-value");
const thresholdsInput = document.getElementById("thresholds");
const gridPointsInput = document.getElementById("grid-points");
const gridPointsOutput = document.getElementById("grid-points-output");
const naturalAxisInput = document.getElementById("display-natural-axis");
const showCutoffsInput = document.getElementById("show-cutoffs");
const exportPngButton = document.getElementById("export-png");
const exportCsvButton = document.getElementById("export-csv");

const runtimeState = {
  readyPromise: null,
  pyodide: null,
  computeCurvesJson: null,
  currentResponse: null,
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
}

function clearRenderedState() {
  runtimeState.currentResponse = null;
  summaryGrid.innerHTML = "";
  commentaryText.textContent = "";
  warningsList.innerHTML = "";
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

function formatRange(values) {
  if (!Array.isArray(values) || values.length !== 2) {
    return "";
  }
  return `${formatNumber(values[0])} to ${formatNumber(values[1])}`;
}

function estimateSourceLabel(estimateSource) {
  return estimateSource === "provided_validated"
    ? "Provided and validated"
    : "CI-implied from 95% CI";
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

  naturalAxisInput.disabled = effect.family !== "ratio";
  if (effect.family !== "ratio") {
    naturalAxisInput.checked = false;
  } else if (!naturalAxisInput.checked) {
    naturalAxisInput.checked = true;
  }
}

function buildPayload() {
  return {
    effect_type: effectTypeSelect.value,
    estimate: parseOptionalNumber(estimateInput.value),
    lower: parseOptionalNumber(lowerInput.value),
    upper: parseOptionalNumber(upperInput.value),
    null_value: parseOptionalNumber(nullInput.value),
    thresholds: parseThresholds(thresholdsInput.value),
    display_natural_axis: naturalAxisInput.checked,
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
  const items = [
    ["Estimate", response.summary.estimate_display],
    ["Estimate source", estimateSourceLabel(response.meta.estimate_source)],
    ["95% CI", `${formatNumber(response.summary.ci_display[0])} to ${formatNumber(response.summary.ci_display[1])}`],
    ["Working-scale SE", response.summary.working_scale_se],
    ["Critical effect markers", formatRange(response.summary.critical_effect_markers_display)],
    ["Null relative likelihood", response.summary.null_relative_likelihood],
    ["MLE:null likelihood ratio", formatLikelihoodRatio(response.summary)],
    ["Two-sided Wald p-value", response.summary.two_sided_wald_p_value],
  ];

  summaryGrid.innerHTML = items
    .map(
      ([label, value]) => `
        <div class="summary-item">
          <span class="summary-label">${label}</span>
          <span class="summary-value">${typeof value === "number" ? formatNumber(value) : value}</span>
        </div>
      `,
    )
    .join("");
}

function renderCommentary(response) {
  const nullValue = formatNumber(response.summary.null_display);
  const estimateClause =
    response.meta.estimate_source === "provided_validated"
      ? "The supplied point estimate matched the 95% CI within rounding tolerance, and the plotted estimate uses the CI-implied midpoint on the working scale."
      : "No point estimate was supplied, so the plotted estimate is the CI-implied midpoint of the 95% CI on the working scale.";
  const likelihoodRatioClause =
    response.summary.likelihood_ratio_mle_to_null === null
      ? `Because the null value is ${nullValue}, the implied MLE:null likelihood ratio exceeds browser floating-point range.`
      : `Because the null value is ${nullValue}, the observed data are ${formatLikelihoodRatio(response.summary)} times as compatible with the CI-implied estimate as with the null.`;
  commentaryText.textContent =
    `These two panels summarize the same Wald approximation in two different ways. ` +
    `The top panel shows how compatible each effect size is with the CI-driven estimate using the two-sided Wald p-value scale. ` +
    `The bottom panel shows the same information as a normalized relative likelihood curve, which peaks at the CI-implied estimate. ` +
    `${estimateClause} ` +
    `The paired critical-effect markers show the alpha=0.05, power=0.80 distance around the null. ` +
    `${likelihoodRatioClause} ` +
    `This display is reconstructed from the confidence interval, so it is an approximation rather than the exact profile likelihood from the fitted model.`;
}

function renderWarnings(response) {
  const notes = [
    response.meta.effect_spec.family === "ratio"
      ? "Computations are performed on the log scale and optionally displayed back on the natural ratio scale."
      : "Computations are performed on the natural additive working scale.",
    `Standard error reconstruction method: ${response.meta.se_method}.`,
  ];
  if (response.meta.show_cutoffs) {
    notes.push("Horizontal guide lines mark 90%, 95%, and 99% confidence cutoffs.");
  }
  const messages = [...notes, ...response.warnings];

  warningsList.innerHTML = messages.map((message) => `<li>${message}</li>`).join("");
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
    await ensureRuntime();
    setStatus("loading", "Computing Wald confidence and likelihood curves.");
    const resultJson = runtimeState.computeCurvesJson(JSON.stringify(payload));
    const response = JSON.parse(resultJson);
    runtimeState.currentResponse = response;

    renderSummary(response);
    renderCommentary(response);
    renderWarnings(response);
    await renderCurves(plotElement, response);
    setExportEnabled(true);
    setStatus("ready", "Curves updated.");
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
  naturalAxisInput.checked = DEFAULT_VALUES.display_natural_axis;
  gridPointsInput.value = DEFAULT_VALUES.grid_points;
  gridPointsOutput.value = DEFAULT_VALUES.grid_points;
  gridPointsOutput.textContent = DEFAULT_VALUES.grid_points;
  showCutoffsInput.checked = DEFAULT_VALUES.show_cutoffs;
  runtimeState.lastDefaultNull = getSelectedEffect().defaultNull;

  updateEffectControls();
}

function initializeUi() {
  sidebar.dataset.collapsed = "false";
  setExportEnabled(false);
  toggleButton.addEventListener("click", () => {
    const nextCollapsed = sidebar.dataset.collapsed !== "true";
    sidebar.dataset.collapsed = nextCollapsed ? "true" : "false";
    toggleButton.setAttribute("aria-expanded", String(!nextCollapsed));
  });

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
}

initializeForm();
initializeUi();
setStatus("loading", "Preparing browser runtime and first render.");
scheduleCompute();
