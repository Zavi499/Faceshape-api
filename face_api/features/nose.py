"""Nose feature classification."""

from __future__ import annotations

from measurements import MeasurementResult


def analyze_nose(measurements: MeasurementResult) -> dict[str, float | str]:
    """Classify nose width, length, bridge, and shape."""

    width_ratio = measurements.nose_width / max(measurements.face_width, 1e-6)
    length_ratio = measurements.nose_length / max(measurements.face_height, 1e-6)
    bridge_ratio = measurements.bridge_height / max(measurements.nose_length, 1e-6)

    if width_ratio < 0.25:
        width = "Narrow"
    elif width_ratio <= 0.35:
        width = "Medium"
    else:
        width = "Wide"

    if length_ratio < 0.28:
        length = "Short"
    elif length_ratio <= 0.38:
        length = "Medium"
    else:
        length = "Long"

    if bridge_ratio < 0.55:
        bridge = "Low"
    elif bridge_ratio <= 0.75:
        bridge = "Medium"
    else:
        bridge = "Very high"

    if bridge == "Very high" and width == "Narrow":
        shape = "Aquiline"
    elif bridge == "Low" and width == "Wide":
        shape = "Broad"
    elif bridge == "Low" and width == "Narrow":
        shape = "Button"
    else:
        shape = "Straight"

    if abs(width_ratio - 0.30) <= 0.04 and abs(length_ratio - 0.33) <= 0.04:
        proportion = "Balanced"
    elif abs(width_ratio - 0.30) <= 0.08 and abs(length_ratio - 0.33) <= 0.08:
        proportion = "Harmonious"
    else:
        proportion = "Distinctive"

    return {
        "width": width,
        "length": length,
        "bridge": bridge,
        "shape": shape,
        "proportion": proportion,
        "width_ratio": round(width_ratio, 2),
        "length_ratio": round(length_ratio, 2),
        "bridge_ratio": round(bridge_ratio, 2),
    }
