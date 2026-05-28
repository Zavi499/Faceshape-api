"""Eyebrow feature classification."""

from __future__ import annotations

from config import BROW_LEFT, BROW_RIGHT
from measurements import MeasurementResult


def analyze_eyebrows(
    measurements: MeasurementResult,
    pixel_landmarks: dict[int, tuple[float, float]],
) -> dict[str, float | str]:
    """Classify eyebrow thickness, arch, spacing, and symmetry."""

    average_height = (measurements.left_brow_height + measurements.right_brow_height) / 2.0
    spacing_ratio = measurements.brow_gap / max(measurements.face_width, 1e-6)
    symmetry_diff_pct = (
        abs(measurements.left_brow_length - measurements.right_brow_length)
        / max(measurements.left_brow_length, measurements.right_brow_length, 1e-6)
    ) * 100.0

    left_arch_delta = (
        (pixel_landmarks[BROW_LEFT[0]][1] + pixel_landmarks[BROW_LEFT[-1]][1]) / 2.0
    ) - pixel_landmarks[BROW_LEFT[2]][1]
    right_arch_delta = (
        (pixel_landmarks[BROW_RIGHT[0]][1] + pixel_landmarks[BROW_RIGHT[-1]][1]) / 2.0
    ) - pixel_landmarks[BROW_RIGHT[2]][1]
    arch_delta = (left_arch_delta + right_arch_delta) / 2.0

    if average_height < 5:
        thickness = "Very Thin"
    elif average_height < 10:
        thickness = "Thin"
    elif average_height <= 15:
        thickness = "Medium"
    else:
        thickness = "Thick"

    if arch_delta < 2:
        arch = "Straight"
    elif arch_delta <= 6:
        arch = "Soft Arch"
    else:
        arch = "High Arch"

    if spacing_ratio < 0.12:
        spacing = "Narrow"
    elif spacing_ratio <= 0.18:
        spacing = "Normal"
    else:
        spacing = "Wide"

    if symmetry_diff_pct < 5:
        symmetry = "Excellent"
    elif symmetry_diff_pct < 10:
        symmetry = "Good"
    else:
        symmetry = "Asymmetric"

    return {
        "thickness": thickness,
        "arch": arch,
        "spacing": spacing,
        "symmetry": symmetry,
        "average_height": round(average_height, 2),
        "spacing_ratio": round(spacing_ratio, 2),
        "arch_delta": round(arch_delta, 2),
        "symmetry_difference_pct": round(symmetry_diff_pct, 2),
    }
