import { effectOptionForKey } from "./config.js";
import {
  effectValueLabel,
  estimateSourceLabel,
  formatLikelihoodRatio,
  formatNumber,
  formatRange,
  supportPhrase,
  thresholdVsNullPhrase,
} from "./formatters.js";

function effectOptionForResponse(response) {
  return effectOptionForKey(response.meta.effect_spec.key);
}

export function buildComparisonTakeaway(response) {
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

export function renderComparisonHeader(response, elements) {
  const effect = effectOptionForResponse(response);
  const hasThresholds = (response.meta.threshold_support_summaries ?? []).length > 0;

  elements.plotTitle.textContent = `How the data compare candidate ${effect.candidateLabel}`;
  elements.plotSubtitle.textContent = hasThresholds
    ? `Relative to the null ${effect.shortLabel} = ${formatNumber(response.summary.null_display)} and clinical thresholds`
    : "Relative to the null and the CI-implied estimate";
  elements.comparisonTakeaway.textContent = buildComparisonTakeaway(response);
}

export function buildFigureCaption(response, displayOptions) {
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

export function renderSummary(response, summaryGrid) {
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

export function hasCompatibilityPanel(viewMode) {
  return viewMode !== "likelihood";
}

export function renderPlotKey(response, displayOptions, plotKey) {
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

export function renderCommentary(response, displayOptions, commentaryText) {
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

export function renderWarnings(response, displayOptions, warningsList) {
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

function csvValue(value) {
  if (Number.isFinite(value)) {
    return String(value);
  }
  return `"${String(value)}"`;
}

export function buildCsv(response) {
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
    rows.push(headers.map((header) => csvValue(response.grid[header][index])).join(","));
  }

  return `${rows.join("\n")}\n`;
}
