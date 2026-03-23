from __future__ import annotations

import json

from confcurve.web_contract import compute_curves


def test_compute_curves_response_is_json_serializable() -> None:
    response = compute_curves(
        {
            "effect_type": "mean_difference",
            "estimate": 0.42,
            "lower": 0.11,
            "upper": 0.73,
            "grid_points": 401,
        }
    )

    payload = json.loads(json.dumps(response))
    assert payload["meta"]["grid_points"] == 401
    assert list(payload["grid"]) == [
        "effect_display",
        "effect_working",
        "z",
        "compatibility",
        "relative_likelihood",
        "log_relative_likelihood",
    ]
    assert len(payload["grid"]["effect_display"]) == 401
