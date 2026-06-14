export const PYODIDE_VERSION = "0.29.3";
export const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
export const PYTHON_PACKAGE_FILES = [
  "__init__.py",
  "core.py",
  "design.py",
  "models.py",
  "stage.py",
  "web_contract.py",
];
export const DEFAULT_VIEW_MODE = "both";

export const DESIGN_SELECTION_RULE_OPTIONS = [
  {
    key: "two_sided_p_lt_alpha",
    label: "Two-sided p < alpha against the null",
    usesDirection: false,
    usesThreshold: false,
  },
  {
    key: "one_sided_positive_p_lt_alpha",
    label: "One-sided positive p < alpha",
    usesDirection: false,
    usesThreshold: false,
  },
  {
    key: "one_sided_negative_p_lt_alpha",
    label: "One-sided negative p < alpha",
    usesDirection: false,
    usesThreshold: false,
  },
  {
    key: "ci_excludes_null_in_beneficial_direction",
    label: "CI at selected alpha excludes null in selected direction",
    usesDirection: true,
    usesThreshold: false,
  },
  {
    key: "estimate_exceeds_mcid_and_p_lt_alpha",
    label: "Estimate exceeds threshold and p < alpha",
    usesDirection: true,
    usesThreshold: true,
  },
  {
    key: "ci_excludes_mcid",
    label: "CI at selected alpha excludes claim threshold",
    usesDirection: true,
    usesThreshold: true,
  },
];

export const DESIGN_METRIC_OPTIONS = [
  {
    key: "power",
    label: "Power",
    field: "power",
  },
  {
    key: "type_s",
    label: "Type S probability",
    field: "type_s",
  },
  {
    key: "type_m",
    label: "Type M exaggeration",
    field: "type_m",
  },
  {
    key: "observed_exaggeration",
    label: "Observed exaggeration if true",
    field: "observed_exaggeration",
  },
];

export const EFFECT_OPTIONS = [
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

export const DEFAULT_VALUES = {
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
  design_enabled: false,
  design_alpha: "0.05",
  design_selection_rule: "two_sided_p_lt_alpha",
  design_claim_direction: "positive",
  design_claim_threshold: "",
  design_information_multiplier: "1",
  design_precision_target_effect: "",
  design_target_power: "0.80",
  design_max_type_s: "",
  design_max_type_m: "",
  design_true_effects: "",
  design_plausible_range_lower: "",
  design_plausible_range_upper: "",
};

export function effectOptionForKey(effectKey) {
  return EFFECT_OPTIONS.find((option) => option.key === effectKey) ?? EFFECT_OPTIONS[0];
}

export function designMetricOptionForKey(metricKey) {
  return (
    DESIGN_METRIC_OPTIONS.find((option) => option.key === metricKey) ?? DESIGN_METRIC_OPTIONS[0]
  );
}
