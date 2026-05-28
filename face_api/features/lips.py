"""Lip feature classification."""

from __future__ import annotations

from measurements import MeasurementResult


def analyze_lips(measurements: MeasurementResult) -> dict[str, float | str]:
    """Classify lip width, thickness, shape, cupid bow, and balance."""

    width_ratio = measurements.mouth_width / max(measurements.face_width, 1e-6)
    total_thickness = measurements.upper_lip_height + measurements.lower_lip_height
    upper_lower_ratio = measurements.upper_to_lower_ratio
    cupid_bow_offset = measurements.cupid_bow_offset
    symmetry_difference = measurements.lip_corner_diff

    if width_ratio < 0.38:
        width = "Narrow"
    elif width_ratio <= 0.52:
        width = "Medium"
    else:
        width = "Wide"

    if total_thickness < 16:
        thickness = "Thin"
    elif total_thickness <= 24:
        thickness = "Medium"
    else:
        thickness = "Full"

    if upper_lower_ratio > 1.5:
        shape = "Top-heavy"
    elif upper_lower_ratio >= 0.8:
        shape = "Balanced"
    else:
        shape = "Bottom-heavy"

    cupid_bow = "Defined" if cupid_bow_offset > 4 else "Subtle"

    if symmetry_difference < 3:
        symmetry = "Excellent"
    elif symmetry_difference < 6:
        symmetry = "Good"
    else:
        symmetry = "Asymmetric"

    if abs(width_ratio - 0.50) <= 0.05:
        proportion = "Balanced"
    elif abs(width_ratio - 0.50) <= 0.10:
        proportion = "Harmonious"
    else:
        proportion = "Distinctive"

    return {
        "width": width,
        "thickness": thickness,
        "shape": shape,
        "cupid_bow": cupid_bow,
        "symmetry": symmetry,
        "proportion": proportion,
        "width_ratio": round(width_ratio, 2),
        "total_thickness": round(total_thickness, 2),
        "upper_lower_ratio": round(upper_lower_ratio, 2),
        "cupid_bow_offset": round(cupid_bow_offset, 2),
        "symmetry_difference": round(symmetry_difference, 2),
    }
