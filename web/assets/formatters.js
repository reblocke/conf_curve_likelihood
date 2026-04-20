export function formatNumber(value) {
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

export function formatLikelihoodRatio(summary) {
  if (summary.likelihood_ratio_mle_to_null !== null) {
    return formatNumber(summary.likelihood_ratio_mle_to_null);
  }
  if (summary.log_likelihood_ratio_mle_to_null === null) {
    return "Overflow";
  }
  const log10LikelihoodRatio = summary.log_likelihood_ratio_mle_to_null / Math.LN10;
  return `Overflow (log10 LR ${formatNumber(log10LikelihoodRatio)})`;
}

export function formatOptionalLikelihoodRatio(value, logValue) {
  if (value !== null) {
    return `${formatNumber(value)}x`;
  }
  if (logValue === null) {
    return "not finite";
  }
  const log10LikelihoodRatio = logValue / Math.LN10;
  return `log10 ratio ${formatNumber(log10LikelihoodRatio)}`;
}

export function formatRange(values) {
  if (!Array.isArray(values) || values.length !== 2) {
    return "";
  }
  return `${formatNumber(values[0])} to ${formatNumber(values[1])}`;
}

export function estimateSourceLabel(estimateSource) {
  return estimateSource === "provided_validated"
    ? "Provided and validated"
    : "CI-implied from 95% CI";
}

export function effectValueLabel(effect, value) {
  return `${effect.shortLabel} = ${formatNumber(value)}`;
}

export function supportPhrase(relativeLikelihood) {
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

export function thresholdVsNullPhrase(thresholdSummary) {
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
