"""Facial symmetry scoring utilities."""

from __future__ import annotations

from measurements import MeasurementResult


def compute_pair_score(left_value: float, right_value: float) -> float:
    """Compute the normalized symmetry score for a left-right pair."""

    if max(left_value, right_value) == 0:
        return 0.0
    score = (1.0 - abs(left_value - right_value) / max(left_value, right_value)) * 100.0
    return round(max(score, 0.0), 2)


def compute_symmetry(measurements: MeasurementResult) -> dict[str, float]:
    """Compute the aggregate symmetry score across eyes, brows, and jaw."""

    eye_width_score = compute_pair_score(measurements.left_eye_width, measurements.right_eye_width)
    brow_length_score = compute_pair_score(measurements.left_brow_length, measurements.right_brow_length)
    jaw_balance_score = compute_pair_score(measurements.jaw_half_width_left, measurements.jaw_half_width_right)
    symmetry_score = round((eye_width_score + brow_length_score + jaw_balance_score) / 3.0, 2)
    return {
        "eye_width_score": eye_width_score,
        "brow_length_score": brow_length_score,
        "jaw_balance_score": jaw_balance_score,
        "symmetry_score": symmetry_score,
    }
