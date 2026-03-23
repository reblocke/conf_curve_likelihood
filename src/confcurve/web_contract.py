from __future__ import annotations

from .models import CurveRequest, CurveResponse


def compute_curves(payload: CurveRequest) -> CurveResponse:
    """Return a placeholder response until the numerical engine is wired."""

    _ = payload
    return {
        "meta": {"status": "placeholder"},
        "summary": {},
        "warnings": ["Numerical core has not been staged into the browser yet."],
        "grid": {},
    }
