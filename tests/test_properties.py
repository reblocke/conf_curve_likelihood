from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from confcurve.core import (
    LOG_MAX_FLOAT,
    ValidationError,
    confidence_curve,
    from_working_scale,
    relative_likelihood,
    summaries,
    to_working_scale,
    validate_inputs,
)

FINITE_FLOATS = st.floats(allow_nan=False, allow_infinity=False, width=32)
POSITIVE_FLOATS = st.floats(min_value=1e-4, max_value=20.0, allow_nan=False, allow_infinity=False)


@given(
    theta_hat=FINITE_FLOATS,
    se=st.floats(min_value=0.05, max_value=3.0),
    distance=st.floats(min_value=0.0, max_value=6.0),
)
def test_curves_are_symmetric_around_the_mle(theta_hat: float, se: float, distance: float) -> None:
    left = theta_hat - (distance * se)
    right = theta_hat + (distance * se)

    assert confidence_curve(left, theta_hat=theta_hat, se=se).item() == pytest.approx(
        confidence_curve(right, theta_hat=theta_hat, se=se).item()
    )
    assert relative_likelihood(left, theta_hat=theta_hat, se=se).item() == pytest.approx(
        relative_likelihood(right, theta_hat=theta_hat, se=se).item()
    )


@given(
    theta_hat=FINITE_FLOATS,
    se=st.floats(min_value=0.05, max_value=3.0),
    distance_1=st.floats(min_value=0.01, max_value=2.5),
    distance_2=st.floats(min_value=2.6, max_value=6.0),
)
def test_curves_decline_as_distance_from_the_mle_increases(
    theta_hat: float,
    se: float,
    distance_1: float,
    distance_2: float,
) -> None:
    theta_1 = theta_hat + (distance_1 * se)
    theta_2 = theta_hat + (distance_2 * se)

    assert (
        confidence_curve(theta_1, theta_hat=theta_hat, se=se).item()
        >= confidence_curve(theta_2, theta_hat=theta_hat, se=se).item()
    )
    assert (
        relative_likelihood(theta_1, theta_hat=theta_hat, se=se).item()
        >= relative_likelihood(theta_2, theta_hat=theta_hat, se=se).item()
    )


@given(POSITIVE_FLOATS)
def test_ratio_scale_round_trip_is_stable(value: float) -> None:
    assert from_working_scale("odds_ratio", to_working_scale("odds_ratio", value)) == pytest.approx(
        value
    )


@given(nonpositive=st.floats(max_value=0.0, allow_nan=False, allow_infinity=False))
def test_invalid_ratio_inputs_fail_fast(nonpositive: float) -> None:
    with pytest.raises(ValidationError):
        validate_inputs("risk_ratio", estimate=1.2, lower=nonpositive, upper=2.0)


@given(
    theta_hat=FINITE_FLOATS, se=st.floats(min_value=0.05, max_value=3.0), null_value=FINITE_FLOATS
)
def test_null_likelihood_ratio_matches_inverse_relative_likelihood(
    theta_hat: float,
    se: float,
    null_value: float,
) -> None:
    stats = summaries(theta_hat=theta_hat, se=se, null_value=null_value)

    if stats["null_relative_likelihood"] == 0.0:
        assert stats["likelihood_ratio_mle_to_null"] is None
        if stats["log_likelihood_ratio_mle_to_null"] is None:
            assert stats["log_null_relative_likelihood"] is None
        else:
            assert stats["log_likelihood_ratio_mle_to_null"] > LOG_MAX_FLOAT
    else:
        assert stats["likelihood_ratio_mle_to_null"] == pytest.approx(
            1.0 / stats["null_relative_likelihood"]
        )
