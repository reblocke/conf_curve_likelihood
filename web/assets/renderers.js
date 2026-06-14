import { effectOptionForKey } from "./config.js";
import {
  effectValueLabel,
  estimateSourceLabel,
  formatLikelihoodRatio,
  formatNumber,
  formatPercent,
  formatRange,
  formatRatio,
  supportPhrase,
  thresholdVsNullPhrase,
} from "./formatters.js";

const DESIGN_RATIO_DISPLAY_CAP = 10;

function effectOptionForResponse(response) {
  return effectOptionForKey(response.meta.effect_spec.key);
}

function hasDesign(response) {
  return response.design?.config?.enabled === true;
}

function hasRatioDesignPlotOmissions(response) {
  if (!hasDesign(response)) {
    return false;
  }
  return ["type_m", "observed_exaggeration"].some((field) =>
    response.design.grid[field].some(
      (value) => Number.isFinite(value) && value > DESIGN_RATIO_DISPLAY_CAP,
    ),
  );
}

function sourceLabel(source) {
  if (source === "null") {
    return "Null";
  }
  if (source === "ci_implied_estimate") {
    return "CI-implied estimate";
  }
  if (source === "threshold") {
    return "Reference threshold / MCID";
  }
  return "Custom assumed true effect";
}

function selectedScenarioIndex(scenarios, requestedValue) {
  const requestedIndex = Number(requestedValue);
  if (
    Number.isInteger(requestedIndex) &&
    requestedIndex >= 0 &&
    requestedIndex < scenarios.length
  ) {
    return requestedIndex;
  }
  const customIndex = scenarios.findIndex((scenario) => scenario.source === "custom_true_effect");
  if (customIndex >= 0) {
    return customIndex;
  }
  const thresholdIndex = scenarios.findIndex((scenario) => scenario.source === "threshold");
  if (thresholdIndex >= 0) {
    return thresholdIndex;
  }
  const estimateIndex = scenarios.findIndex(
    (scenario) => scenario.source === "ci_implied_estimate",
  );
  return estimateIndex >= 0 ? estimateIndex : 0;
}

function optionalPercent(value) {
  return value === null ? "undefined" : formatPercent(value);
}

function optionalRatio(value) {
  return value === null ? "undefined" : formatRatio(value);
}

function optionalNumber(value) {
  return value === null || value === undefined ? "not available" : formatNumber(value);
}

function optionalCiWidth(value) {
  return value === null || value === undefined ? "not available" : formatNumber(value);
}

function buildReviewerText(response, scenario) {
  const design = response.design;
  const effect = effectOptionForResponse(response);
  const trueEffect = effectValueLabel(effect, scenario.true_effect_display);
  const scaleLabel = response.meta.effect_spec.working_scale === "log" ? "log" : "working";
  const alpha = formatNumber(design.config.alpha);
  const rule = design.config.selection_rule_label;
  const informationMultiplier = formatRatio(design.config.information_multiplier);
  const firstPrecisionTarget = design.precision_targets?.[0];
  const precisionSentence = firstPrecisionTarget
    ? firstPrecisionTarget.required_information_multiplier === null
      ? ` The precision target table did not find a finite solution for ${firstPrecisionTarget.target.toLowerCase()} under this rule.`
      : ` For the selected precision target effect, the ${firstPrecisionTarget.target.toLowerCase()} target requires about ${formatRatio(firstPrecisionTarget.required_information_multiplier)} the current information.`
    : "";

  if (scenario.type_s === null || scenario.type_m === null) {
    return (
      `Using ${informationMultiplier} the CI-implied Wald information and assuming a true effect of ${trueEffect}, ` +
      `this design would have ${formatPercent(scenario.power)} selected-claim probability under ${rule} at alpha ${alpha}. ` +
      "Because the assumed true effect is at or very near the null, Type S and Type M are " +
      "undefined or unstable; interpret only the power/type-I-error behavior at the null. " +
      "These are repeated-study operating characteristics under the assumed true effect, not posterior probabilities that the observed result is wrong." +
      precisionSentence
    );
  }

  return (
    `Using ${informationMultiplier} the CI-implied Wald information and assuming a true effect of ${trueEffect}, ` +
    `this design would have ${formatPercent(scenario.power)} selected-claim probability under ${rule} at alpha ${alpha}. ` +
    `Conditional on a selected claim, the wrong-sign probability would be ${formatPercent(scenario.type_s)} ` +
    `and the expected magnitude exaggeration would be ${formatRatio(scenario.type_m)} on the ${scaleLabel} scale. ` +
    "These are repeated-study operating characteristics under the assumed true effect, not posterior probabilities that the observed result is wrong." +
    precisionSentence
  );
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
    takeaway += ` The reference threshold / MCID ${effectValueLabel(effect, thresholdSummary.threshold_display)} ${thresholdVsNullPhrase(thresholdSummary)}.`;
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
    ? `Relative to the null ${effect.shortLabel} = ${formatNumber(response.summary.null_display)} and reference thresholds / MCIDs`
    : "Relative to the null and the CI-implied estimate";
  elements.comparisonTakeaway.textContent = buildComparisonTakeaway(response);
}

export function buildFigureCaption(response, displayOptions) {
  const effect = effectOptionForResponse(response);
  const viewMode = displayOptions.viewMode ?? "both";
  const panelText =
    viewMode === "likelihood"
      ? "The figure shows relative likelihood only."
      : viewMode === "compatibility"
        ? "The figure shows the compatibility curve only."
        : "Panel A shows the compatibility curve and Panel B shows relative likelihood.";
  const thresholdValues = response.meta.thresholds_display ?? [];
  const thresholdText =
    thresholdValues.length > 0
      ? ` Reference thresholds/MCIDs are marked at ${thresholdValues.map(formatNumber).join(", ")}.`
      : "";
  const ciText = hasCompatibilityPanel(viewMode)
    ? " The shaded band on the compatibility panel marks the reported 95% CI."
    : "";
  const sMinus2Text = hasLikelihoodPanel(viewMode)
    ? " The shaded S−2 interval marks candidate effects with relative likelihood at least exp(−2), so the CI-implied estimate is no more than 7.4x as supported."
    : "";
  const designText = hasDesign(response)
    ? ` The design-calibration panels treat each x-axis value as an assumed true effect and show repeated-study operating characteristics under ${response.design.config.selection_rule_label} with ${formatRatio(response.design.config.information_multiplier)} the CI-implied information.`
    : "";

  return (
    `Figure. Wald reconstruction from the reported 95% CI (${formatRange(response.summary.ci_display)}) for ${effect.label.toLowerCase()}. ` +
    `The CI-implied point estimate is ${effectValueLabel(effect, response.summary.estimate_display)} and the null is ${effectValueLabel(effect, response.summary.null_display)}. ` +
    `${panelText} Relative likelihood is normalized to 1 at the CI-implied estimate; compatibility is the two-sided Wald p-value function across candidate effect sizes.` +
    `${ciText}${sMinus2Text}${thresholdText}${designText} This is not exact fitted-model profile likelihood.`
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
    ["80% power benchmarks", formatRange(response.summary.critical_effect_markers_display)],
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
  ];
  if (hasDesign(response)) {
    groups.push({
      title: "Design calibration",
      items: [
        ["Selection alpha", response.design.config.alpha],
        ["Selection rule", response.design.config.selection_rule_label],
        ["Claim direction", response.design.config.claim_direction],
        ["Information multiplier", formatRatio(response.design.config.information_multiplier)],
        ["Current SE", response.design.config.current_se_working],
        ["Design SE", response.design.config.design_se_working],
        ["Approx design 95% CI width", response.design.config.approx_design_ci_width_working],
        ["Type M scale", response.design.config.type_m_scale_note],
      ],
    });
  }
  groups.push({
      title: "Technical reconstruction",
      items: technicalItems,
    });

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

export function hasLikelihoodPanel(viewMode) {
  return viewMode !== "compatibility";
}

export function renderPlotKey(response, displayOptions, plotKey) {
  const viewMode = displayOptions.viewMode ?? "both";
  const keyRows = [
    ["estimate", "Point estimate"],
    ["null", "Null value"],
    ["critical", "80% power benchmarks"],
  ];
  if (hasCompatibilityPanel(viewMode)) {
    keyRows.push(["ci", "Reported 95% CI"]);
  }
  if (hasLikelihoodPanel(viewMode)) {
    keyRows.push(["s-minus-2", "S−2 support interval"]);
  }
  if (response.meta.thresholds_display.length > 0) {
    keyRows.push(["threshold", "Reference thresholds / MCIDs"]);
  }
  if (hasDesign(response) && response.design.config.claim_threshold_display !== null) {
    keyRows.push(["claim-threshold", "Claim threshold for selected-claim rule"]);
  }
  if (response.meta.show_cutoffs && hasCompatibilityPanel(viewMode)) {
    keyRows.push(["cutoff", "Compatibility cutoffs"]);
  }
  if (hasDesign(response)) {
    keyRows.push(["design", "Design calibration panels"]);
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
  const designClause = hasDesign(response)
    ? `Design calibration treats candidate x-axis values as assumed true effects under ${response.design.config.selection_rule_label}; the information multiplier changes only design calculations and does not revise the observed compatibility or likelihood curves.`
    : "";
  commentaryText.textContent =
    `${viewClause} ` +
    `${estimateClause} ` +
    `${spacingClause} ` +
    `The paired 80% power benchmark markers show the alpha=0.05, power=0.80 distance around the null. ` +
    `${likelihoodRatioClause} ` +
    `${designClause} ` +
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
    notes.push("Reference thresholds/MCIDs are shown as dashed green vertical reference lines.");
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
  if (hasLikelihoodPanel(displayOptions.viewMode)) {
    notes.push(
      "The S−2 support interval marks relative likelihood >= exp(−2), equivalent to an MLE:candidate likelihood ratio <= exp(2).",
    );
  }
  if (hasDesign(response)) {
    if (hasRatioDesignPlotOmissions(response)) {
      notes.push(
        "In ratio panels, 1x means no exaggeration and 2x means a two-fold magnitude overestimate; values above 10x are omitted from the plotted curve.",
      );
    }
    notes.push(...response.design.warnings);
  }
  const messages = [...notes, ...response.warnings];

  warningsList.innerHTML = messages.map((message) => `<li>${message}</li>`).join("");
}

function csvValue(value) {
  if (value === null || value === undefined) {
    return "";
  }
  if (Number.isFinite(value)) {
    return String(value);
  }
  return `"${String(value)}"`;
}

export function buildCsv(response) {
  const observedHeaders = [
    "effect_display",
    "effect_working",
    "z",
    "compatibility",
    "relative_likelihood",
    "log_relative_likelihood",
  ];
  const designHeaders = hasDesign(response)
    ? [
        "design_selection_rule",
        "design_claim_direction",
        "design_information_multiplier",
        "design_claim_threshold_working",
        "design_delta_if_true",
        "design_power_if_true",
        "design_type_s_if_true",
        "design_type_m_if_true",
        "design_expected_selected_abs_z_if_true",
        "design_observed_exaggeration_if_true",
      ]
    : [];
  const headers = [...observedHeaders, ...designHeaders];
  const rows = [headers.join(",")];

  for (let index = 0; index < response.grid.effect_display.length; index += 1) {
    const observedValues = observedHeaders.map((header) => response.grid[header][index]);
    const designValues = hasDesign(response)
      ? [
          response.design.config.selection_rule,
          response.design.config.claim_direction,
          response.design.config.information_multiplier,
          response.design.config.claim_threshold_working,
          response.design.grid.delta[index],
          response.design.grid.power[index],
          response.design.grid.type_s[index],
          response.design.grid.type_m[index],
          response.design.grid.expected_selected_abs_z[index],
          response.design.grid.observed_exaggeration[index],
        ]
      : [];
    rows.push([...observedValues, ...designValues].map(csvValue).join(","));
  }

  return `${rows.join("\n")}\n`;
}

export function renderDesignResults(response, elements) {
  if (!hasDesign(response)) {
    elements.container.hidden = true;
    elements.summary.textContent = "";
    elements.scenarioTable.innerHTML = "";
    elements.precisionTargetTable.innerHTML = "";
    elements.reviewerScenarioSelect.innerHTML = "";
    elements.reviewerText.textContent = "";
    elements.copyReviewerTextButton.disabled = true;
    return;
  }

  const design = response.design;
  const scenarios = design.scenarios ?? [];
  const selectedIndex = selectedScenarioIndex(scenarios, elements.reviewerScenarioSelect.value);
  const selectedScenario = scenarios[selectedIndex] ?? scenarios[0];
  elements.container.hidden = false;
  elements.summary.textContent =
    `Design calibration enabled: alpha = ${formatNumber(design.config.alpha)}, ` +
    `rule = ${design.config.selection_rule_label}, ` +
    `information = ${formatRatio(design.config.information_multiplier)}. ` +
    "These values are repeated-study operating characteristics.";

  elements.scenarioTable.innerHTML = `
    <table class="design-scenario-table">
      <thead>
        <tr>
          <th>Assumed true effect</th>
          <th>Source / note</th>
          <th>Delta vs null, design SE</th>
          <th>Power</th>
          <th>Type S</th>
          <th>Type M</th>
          <th>Observed exaggeration</th>
        </tr>
      </thead>
      <tbody>
        ${scenarios
          .map(
            (scenario, index) => `
              <tr data-selected="${index === selectedIndex}">
                <td>${formatNumber(scenario.true_effect_display)}</td>
                <td>
                  <strong>${sourceLabel(scenario.source)}</strong>
                  ${scenario.note ? `<span>${scenario.note}</span>` : ""}
                </td>
                <td>${formatNumber(scenario.delta)} SE</td>
                <td>${formatPercent(scenario.power)}</td>
                <td>${optionalPercent(scenario.type_s)}</td>
                <td>${optionalRatio(scenario.type_m)}</td>
                <td>${optionalRatio(scenario.observed_exaggeration)}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;

  const precisionTargets = design.precision_targets ?? [];
  elements.precisionTargetTable.innerHTML =
    precisionTargets.length === 0
      ? ""
      : `
    <table class="design-scenario-table">
      <thead>
        <tr>
          <th>Precision target</th>
          <th>Target true effect</th>
          <th>Required SE</th>
          <th>Required 95% CI width</th>
          <th>Information multiplier</th>
          <th>Achieved metric</th>
          <th>Notes</th>
        </tr>
      </thead>
      <tbody>
        ${precisionTargets
          .map(
            (target) => `
              <tr>
                <td>${target.target}: ${formatNumber(target.requested_value)}</td>
                <td>${formatNumber(target.target_effect_display)}</td>
                <td>${optionalNumber(target.required_se)}</td>
                <td>${optionalCiWidth(target.approx_95_ci_width_working)}</td>
                <td>${optionalRatio(target.required_information_multiplier)}</td>
                <td>
                  Power ${optionalPercent(target.achieved_power)};
                  Type S ${optionalPercent(target.achieved_type_s)};
                  Type M ${optionalRatio(target.achieved_type_m)}
                </td>
                <td>${target.note}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;

  elements.reviewerScenarioSelect.innerHTML = scenarios
    .map(
      (scenario, index) =>
        `<option value="${index}">${scenario.label}${
          scenario.source === "ci_implied_estimate" ? " (optimistic)" : ""
        }</option>`,
    )
    .join("");
  elements.reviewerScenarioSelect.value = String(selectedIndex);
  elements.reviewerText.textContent = buildReviewerText(response, selectedScenario);
  elements.copyReviewerTextButton.disabled = false;
}
