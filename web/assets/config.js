export const PYODIDE_VERSION = "0.29.3";
export const PYODIDE_INDEX_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
export const PYTHON_PACKAGE_FILES = [
  "__init__.py",
  "core.py",
  "models.py",
  "stage.py",
  "web_contract.py",
];
export const DEFAULT_VIEW_MODE = "both";

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
};

export function effectOptionForKey(effectKey) {
  return EFFECT_OPTIONS.find((option) => option.key === effectKey) ?? EFFECT_OPTIONS[0];
}
