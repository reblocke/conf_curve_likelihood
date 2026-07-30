# ADR 0001: Reject unrepresentable design distances and enforce strict browser JSON

- Status: accepted
- Date: 2026-07-29

## Context

Finite design inputs near the limits of binary64 arithmetic can overflow during subtraction or
division. The resulting infinity can reach the browser response even though every submitted value
was finite. JavaScript then receives non-standard JSON tokens, and the failure appears as a parsing
error instead of a scientific-input validation error.

## Decision

Compute standardized design distances with the existing direct arithmetic for ordinary inputs. If
subtracting finite values overflows, retry only those elements with exact power-of-two scaling before
division. Reject a distance with `ValidationError` if the result still cannot be represented as a
finite binary64 value.

Use the same calculation for true-effect and claim-threshold distances. Preserve the direct
observed-exaggeration calculation when both raw distances are finite; if either subtraction
overflows, calculate the ratio from common power-of-two-scaled raw distances. Reject an
observed-exaggeration ratio that remains unrepresentable.

Validate every completed response recursively and require `allow_nan=False` when the Pyodide bridge
serializes it. This makes the Python contract fail with `ValidationError` and leaves a second defense
before JavaScript parsing if any future path produces a non-finite number.

## Consequences

- Ordinary finite inputs retain the existing arithmetic path and results.
- Representable standardized distances survive opposite-sign subtraction overflow.
- Inputs whose requested design distance or observed-exaggeration ratio exceeds binary64 range
  produce an explicit validation error instead of invalid browser JSON.
- The public JSON contract is strict: `NaN`, positive infinity, and negative infinity are forbidden
  in every successful response.

## Alternatives Considered

- Replace non-finite values with JSON `null`: rejected because it would hide an unsupported
  scientific calculation.
- Clip distances to the largest finite value: rejected because it would silently change the
  requested effect distance.
- Depend on platform-specific extended precision: rejected because browser and native runtimes must
  behave consistently.

## Validation

Unit tests cover ordinary-path equivalence, representable subtraction overflow, unrepresentable
division overflow, threshold distances, subnormal values, null summaries, and
observed-exaggeration fallback. Integration and browser tests cover the original finite-input
failure, unrepresentable derived widths, completed-response validation, and the strict serializer.
