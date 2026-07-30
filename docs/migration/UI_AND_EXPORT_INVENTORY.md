# UI and Export Inventory

This document records the integrated browser UI and export contract at final behavior source
commit `830756ecb11b4e8161f8dfe1fc75afc346ef4467`. Defaults come from
`web/assets/config.js`; dynamic behavior comes from `web/assets/app.js`, `renderers.js`, `plot.js`,
and the Python browser contract.

## Controls and defaults

The app recomputes automatically after a 150 ms debounce. It has no submit button. CSV/PNG controls
become available only after Plotly renders successfully. Caption and reviewer-copy controls are
enabled when their text is generated, before the asynchronous Plotly render promise completes.

### Observed-evidence controls

| Control | Default | Current behavior |
|---|---|---|
| Effect measure | Odds ratio | Nine registry choices; determines identity/log working scale and default null |
| Point estimate | blank | Optional validation value; the CI midpoint remains the plotted estimate |
| 95% CI lower | `1.2` | Required finite value |
| 95% CI upper | `2.7` | Required finite value greater than lower |
| Null value | `1` | Dynamic default is 1 for ratios and 0 for additive measures |
| Reference thresholds / MCIDs | blank | Comma/whitespace-separated observed markers and support summaries |
| Enable design calibration | off | Reveals and enables the design controls and appends design outputs |

When the effect family changes, a blank null or a null equal to the previous family default changes
to the new default. A custom null is preserved.

Effect choices appear in this order:

```text
Odds ratio
Risk ratio
Hazard ratio
Incidence rate ratio
Ratio of means
Mean difference
Risk difference
Rate difference
Regression coefficient
```

### Design controls

All design fields are hidden and disabled while design calibration is off.

| Control | Default | Visibility/behavior |
|---|---|---|
| Selection threshold alpha | `0.05` | Must be strictly between 0 and 1 |
| Selection rule | Two-sided `p < alpha` against the null | Six rules listed below |
| Claim direction | positive / above null | Shown for directional CI and threshold rules |
| Claim threshold / MCID | blank | Shown and required only for the two threshold-conditioned rules |
| Information multiplier | `1` | Positive; design SE is current SE divided by its square root |
| Assumed true-effect scenarios | blank | Comma/whitespace-separated scenario rows and precision-target choices |
| Plausible true-effect lower/upper | both blank | Pair required together; shades design panels only |
| Precision target scenario | none | Options are deduplicated reference thresholds and custom true effects |
| Target power | `0.80` | Enabled only after a precision target is selected |
| Maximum Type S | blank | Optional; enabled only with a precision target |
| Maximum Type M | blank | Optional, must be greater than 1; enabled only with a precision target |

Selection-rule options appear in this order:

```text
Two-sided p < alpha against the null
One-sided positive p < alpha
One-sided negative p < alpha
CI at selected alpha excludes null in selected direction
Estimate exceeds threshold and p < alpha
CI at selected alpha excludes claim threshold
```

The one-sided positive and negative rules force their own direction in Python. The direction chooser
is shown for the directional CI rule and both threshold rules. The claim-threshold chooser is shown
only for the last two rules. The current fifth control label says “exceeds,” but for a negative claim
the implemented rule selects an estimate below the claim threshold.

### Advanced display controls

| Control | Default | Current behavior |
|---|---|---|
| Axis spacing | logarithmic | Visible for ratio measures; natural labels with log or linear spacing |
| Plausible display lower/upper | both blank | Pair required together; changes only plot/export x-grid |
| Grid points | `801` | Slider from 201 through 1601 in steps of 200 |
| Compatibility guide lines | on | Shows horizontal 0.10, 0.05, and 0.01 lines when compatibility is visible |

Additive effects hide and disable axis spacing and always display a linear identity-scale axis.

### View and shell controls

- Default view: **Both panels**.
- Alternate views: **Relative likelihood only** and **Compatibility only**.
- The mobile control panel and desktop sidebar can be collapsed without changing inputs.
- Changing view mode rerenders the current response. Changing axis spacing follows the ordinary
  recompute path, but spacing is presentation-only and the scientific response values do not change.
- Missing CI limits show an instruction to enter a 95% CI. Invalid inputs clear the current plot,
  summaries, design tables, caption/reviewer text, and disable exports.
- An extreme finite design request whose standardized distance is not representable raises a
  finite-range validation error. The UI follows its ordinary error path, clears current output, and
  disables exports; non-standard `Infinity` tokens do not reach JavaScript parsing.
- The status card uses `aria-live="polite"`. Controls use associated labels, the view switch is a
  fieldset, and collapse controls expose their state through ARIA attributes.

## Rendered summaries and tables

### Summary cards

The main-comparison group contains:

```text
Point Estimate
95% CI
Null relative likelihood
MLE:null likelihood ratio
Two-sided Wald p-value
one support row for each reference threshold
```

When design is enabled, a design-calibration group is inserted:

```text
Selection alpha
Selection rule
Claim direction
Information multiplier
Current SE
Design SE
Approx design 95% CI width
Type M scale
```

The technical-reconstruction group contains:

```text
Estimate source
Working-scale SE
Computation scale
80% power benchmarks
Display range, when active
```

The page also renders a generated comparison takeaway, interpretation paragraph, plot key, figure
caption, and technical reconstruction notes.

### Design scenario table

When enabled, the scenario table columns are:

```text
Assumed true effect
Source / note
Delta vs null, design SE
Power
Type S
Type M
Observed exaggeration
```

Scenario sources are null, CI-implied estimate, each observed reference threshold, and custom assumed
true effects, with duplicates removed. The CI-implied-estimate row is explicitly labeled
optimistic/circular as an assumed truth.

### Precision-target table

The table is absent until a precision target is selected. Its columns are:

```text
Precision target
Target true effect
Required SE
Required 95% CI width
Information multiplier
Achieved metric
Notes
```

Per-target rows appear in power, maximum Type S, then maximum Type M order when requested. Unavailable
results are shown as “not available” or “undefined,” not zero.

## Plot modes and panels

| View mode | Design off | Design on |
|---|---|---|
| Both panels | A compatibility; B relative likelihood | A and B plus C–F |
| Relative likelihood only | B relative likelihood | B plus C–F |
| Compatibility only | A compatibility | A plus C–F |

The fixed panel meanings are:

```text
A. Observed compatibility: candidate effects compared with the reported CI
B. Observed likelihood: candidate effects compared with the CI-implied estimate
C. Design calibration: selected-claim probability if x is true
D. Design calibration: Type S probability if x is true
E. Design calibration: Type M exaggeration if x is true
F. Design calibration: observed exaggeration if x is true
```

All visible panels share the same numeric x-range. In A/B, x is a candidate effect evaluated against
observed evidence. In C–F, x is an assumed true effect. Ratio effects retain natural-scale x labels;
the selected linear/log spacing affects presentation only.

### Traces and overlays

| Element | Where shown | Behavior |
|---|---|---|
| Compatibility curve | A | Solid line, y range 0 to 1.02 |
| Relative-likelihood curve | B | Normalized to 1; dashed in manuscript mode, otherwise solid |
| Selected-claim probability | C | Labeled Power in the current UI/contract |
| Type S | D | Probability scale 0 to 1.02 |
| Type M | E | X-fold scale; values above 10x omitted from plot only |
| Observed exaggeration | F | X-fold scale; values above 10x omitted from plot only |
| Estimate | Observed zone | Solid vertical marker |
| Null | Observed zone | Dotted vertical marker |
| Paired 80% power benchmarks | Observed zone | Dash-dot vertical markers |
| Reference thresholds / MCIDs | Observed zone | Dashed vertical markers |
| Reported 95% CI | A | Shaded interval clipped to visible x-range |
| 90%, 95%, 99% guides | A | Optional horizontal lines at 0.10, 0.05, and 0.01 |
| S−2 interval | B | Shaded interval plus horizontal `exp(-2)` cutoff |
| Claim threshold | Design zone | Dash-dot vertical marker for threshold rules |
| Plausible true-effect range | C–F | Shaded display-only interval |
| 2x exaggeration guide | E/F | Dotted horizontal visual guide when in range |
| Observed/design separator | Combined design figure | Horizontal separator between conditioning zones |

Marker and interval labels are direct annotations when space permits. Compact layouts retain estimate
and null labels and reduce secondary marker labels. The separate HTML plot key identifies estimate,
null, benchmark, visible CI/S−2, threshold, claim-threshold, and compatibility-cutoff classes as
applicable, plus one generic design-calibration entry. It does not separately key plausible
true-effect shading, 2x guides, or the observed/design separator.

## CSV export

- Button label: **Export CSV**
- Filename: `wald-confidence-curves.csv`
- Encoding/type: UTF-8 text CSV
- Rows: one row per current display grid value, in grid order
- Termination: a final newline is included

Observed-only columns are in this exact order:

```text
effect_display
effect_working
z
compatibility
relative_likelihood
log_relative_likelihood
```

When design calibration is enabled, these columns are appended in this exact order:

```text
design_selection_rule
design_claim_direction
design_information_multiplier
design_claim_threshold_working
design_delta_if_true
design_power_if_true
design_type_s_if_true
design_type_m_if_true
design_expected_selected_abs_z_if_true
design_observed_exaggeration_if_true
```

The first four design values are repeated on every grid row. Undefined values become empty cells.
The CSV does not include the summary cards, threshold-support rows, scenario table, precision-target
table, caption, reviewer text, or warnings.

## PNG exports

Both PNG buttons export the Plotly figure only; the separate HTML caption is not embedded.

| Mode | Filename | Plotly width/height | Scale | Nominal raster size |
|---|---|---|---:|---|
| Dashboard, design off | `wald-confidence-curves.png` | 1400 × 1100 | 2 | 2800 × 2200 px |
| Dashboard, design on | `wald-confidence-curves.png` | 1400 × 1600 | 2 | 2800 × 3200 px |
| Manuscript, design off | `wald-confidence-curves-manuscript.png` | 1400 × 1000 | 2 | 2800 × 2000 px |
| Manuscript, design on | `wald-confidence-curves-manuscript.png` | 1400 × 1500 | 2 | 2800 × 3000 px |

Dashboard export uses the currently rendered view mode and browser styling. Manuscript export
rerenders the same response and view mode in an off-screen fixed-size figure with white backgrounds,
larger manuscript typography/margins, and a dashed relative-likelihood line. Both retain applicable
markers, interval shading, guide lines, panel labels, and design panels.

The implementation requests the listed logical dimensions with Plotly `scale: 2`; the nominal raster
size is the logical size multiplied by two.

## Caption and reviewer-text copy

The generated figure caption changes with the current response and view mode. It records:

- effect measure, reported CI, CI-implied estimate, and null;
- visible compatibility/likelihood panels;
- relative-likelihood normalization and compatibility interpretation;
- reported-CI shading when compatibility is visible;
- S−2 shading when likelihood is visible;
- reference thresholds when supplied;
- design conditioning, selected rule, and information multiplier when enabled; and
- the limitation that the display is not exact fitted-model profile likelihood.

Caption generation is based on view mode and supplied values, not on whether an overlay survives
clipping to a restrictive display range. It can therefore say that CI/S−2 shading or thresholds are
shown even when the corresponding interval or marker is completely outside the visible window.

**Copy caption** uses the Clipboard API when it exists. The temporary-textarea fallback is used only
when `navigator.clipboard` is unavailable, not when an available `writeText()` call rejects.

Reviewer text exists only when design calibration is enabled. On the first design render, the empty
selector value is coerced to scenario index 0, so the null row is initially selected. A valid prior
selection is preserved. If the prior value is not a valid scenario index, the implemented fallback
priority is custom assumed true effect, threshold, CI-implied estimate, then null. The generated
paragraph reports information multiplier, assumed truth, selected-claim probability, selection
rule/alpha, Type S and Type M when defined, and the repeated-study nonposterior limitation. It names
the working/log scale only in the branch where Type M is defined; the near-null branch omits a scale
statement. It also reports the first precision-target result when present. **Copy reviewer text**
uses the Clipboard API and the same unavailable-only fallback behavior as caption copy.

## Privacy posture of UI and exports

- Computation runs in the in-page Pyodide runtime. User values pass to Python as an in-memory JSON
  string, not as a network request.
- Automatic network requests are limited to pinned Pyodide/Plotly and Pyodide package assets plus
  same-origin staged Python files. Numerical inputs are not placed in request URLs or bodies.
- The app does not use query strings, URL fragments, cookies, local/session storage, IndexedDB,
  analytics, telemetry, accounts, or a backend.
- CSV uses a temporary local Blob URL. PNG uses a local data URL. Clipboard writes occur only after
  the corresponding user action.
- The application does not automatically upload or retain export contents. Users remain responsible
  for handling locally downloaded or copied material appropriately.

This posture does not mean the page is network-free: the static CDN requests expose ordinary
connection metadata to the CDN, but they do not contain the entered numerical values.
