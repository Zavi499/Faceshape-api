"""Eye feature classification."""

from __future__ import annotations

from measurements import MeasurementResult


def analyze_eyes(measurements: MeasurementResult) -> dict[str, float | str]:
    """Classify eye size, shape, spacing, and symmetry."""

    mean_width = (measurements.left_eye_width + measurements.right_eye_width) / 2.0
    mean_height = (measurements.left_eye_height + measurements.right_eye_height) / 2.0
    aspect_ratio = mean_width / max(mean_height, 1e-6)
    spacing_ratio = measurements.interocular_distance / max(measurements.face_width, 1e-6)
    symmetry_diff_pct = (
        abs(measurements.left_eye_width - measurements.right_eye_width)
        / max(measurements.left_eye_width, measurements.right_eye_width, 1e-6)
    ) * 100.0

    if mean_width < 20:
        size = "Small"
    elif mean_width <= 27:
        size = "Medium"
    else:
        size = "Large"

    if aspect_ratio < 2.0:
        shape = "Almond"
    elif aspect_ratio <= 2.5:
        shape = "Round"
    else:
        shape = "Wide"

    if spacing_ratio < 0.28:
        spacing = "Close"
    elif spacing_ratio <= 0.32:
        spacing = "Good"
    else:
        spacing = "Wide"

    if symmetry_diff_pct < 5:
        symmetry = "Excellent"
    elif symmetry_diff_pct < 10:
        symmetry = "Good"
    else:
        symmetry = "Asymmetric"

    return {
        "size": size,
        "shape": shape,
        "spacing": spacing,
        "symmetry": symmetry,
        "mean_width": round(mean_width, 2),
        "aspect_ratio": round(aspect_ratio, 2),
        "spacing_ratio": round(spacing_ratio, 2),
        "symmetry_difference_pct": round(symmetry_diff_pct, 2),
    }
