"""Face shape classification and style recommendations."""

from __future__ import annotations

from measurements import MeasurementResult


def _normalize_probabilities(raw_scores: dict[str, float]) -> dict[str, float]:
    """Normalize heuristic face-shape scores so they sum to exactly 100."""

    total = sum(max(score, 0.0) for score in raw_scores.values()) or 1.0
    probabilities = {shape: round((max(score, 0.0) / total) * 100.0, 2) for shape, score in raw_scores.items()}
    difference = round(100.0 - sum(probabilities.values()), 2)
    top_shape = max(probabilities, key=probabilities.get)
    probabilities[top_shape] = round(probabilities[top_shape] + difference, 2)
    return probabilities


def _shape_recommendations(primary_shape: str) -> list[str]:
    """Return three style tips tailored to the primary face shape."""

    recommendations = {
        "Round": [
            "Add height with layered hairstyles or volume on top.",
            "Choose angular eyewear to sharpen soft contours.",
            "Keep beard lines or sideburns tidy to elongate the face.",
        ],
        "Oval": [
            "Most frame shapes suit this balanced profile well.",
            "Use moderate texture in hairstyles to keep proportions natural.",
            "Experiment with both short and medium beard lengths.",
        ],
        "Oblong": [
            "Favor styles with width at the sides instead of extra height.",
            "Use fuller brows or frames to visually shorten the face.",
            "Keep beard bulk near the jawline rather than the chin.",
        ],
        "Square": [
            "Rounder frames soften broad angles nicely.",
            "Textured or side-swept hairstyles reduce boxiness.",
            "A slightly tapered beard helps refine the jawline.",
        ],
        "Heart": [
            "Styles that add fullness around the jaw create balance.",
            "Choose medium-width frames with gentle curves.",
            "Short beard growth around the chin can support the lower face.",
        ],
        "Diamond": [
            "Hairstyles with width at the forehead flatter pronounced cheekbones.",
            "Oval or rimless frames help soften the widest mid-face area.",
            "Keep facial hair neat around the chin to avoid over-narrowing it.",
        ],
    }
    return recommendations[primary_shape]


def analyze_face_shape(measurements: MeasurementResult) -> dict[str, float | str | dict | list[str]]:
    """Classify face shape and build a probability distribution."""

    width_to_length_ratio = measurements.face_width / max(measurements.face_height, 1e-6)
    jaw_ratio = measurements.jaw_width / max(measurements.face_width, 1e-6)
    forehead_ratio = measurements.forehead_width / max(measurements.face_width, 1e-6)

    round_score = max(0.1, 1.0 - abs(width_to_length_ratio - 1.0) * 2.5)
    oval_score = max(0.1, 1.0 - abs(width_to_length_ratio - 0.85) * 3.0 + max(forehead_ratio - jaw_ratio, 0.0))
    oblong_score = max(0.1, 1.0 - abs(width_to_length_ratio - 0.68) * 4.0)
    square_score = max(0.1, (jaw_ratio + forehead_ratio) - abs(jaw_ratio - forehead_ratio) - 0.6)
    heart_score = max(0.1, (forehead_ratio - jaw_ratio) + 0.35)
    diamond_score = max(
        0.1,
        ((measurements.cheekbone_width - measurements.forehead_width) / max(measurements.face_width, 1e-6))
        + ((measurements.cheekbone_width - measurements.jaw_width) / max(measurements.face_width, 1e-6))
        + 0.2,
    )

    if jaw_ratio > 0.85 and forehead_ratio > 0.85 and abs(jaw_ratio - forehead_ratio) < 0.08:
        rule_shape = "Square"
    elif forehead_ratio > jaw_ratio + 0.10:
        rule_shape = "Heart"
    elif measurements.forehead_width < measurements.cheekbone_width and measurements.cheekbone_width > measurements.jaw_width:
        rule_shape = "Diamond"
    elif width_to_length_ratio > 0.95:
        rule_shape = "Round"
    elif width_to_length_ratio < 0.75:
        rule_shape = "Oblong"
    else:
        rule_shape = "Oval"

    raw_scores = {
        "Round": round_score,
        "Oval": oval_score,
        "Oblong": oblong_score,
        "Square": square_score,
        "Heart": heart_score,
        "Diamond": diamond_score,
    }
    raw_scores[rule_shape] += 0.35
    shape_probabilities = _normalize_probabilities(raw_scores)
    primary_shape = max(shape_probabilities, key=shape_probabilities.get)

    top_probability = max(shape_probabilities.values())
    characteristics = {
        "apple_cheeks": "Prominent" if primary_shape in {"Round", "Heart"} else "Subtle",
        "cheekbone": "Pronounced" if primary_shape in {"Diamond", "Heart"} else "Balanced",
        "chin": "Pointed" if primary_shape in {"Heart", "Diamond"} else "Rounded" if primary_shape in {"Round", "Oval"} else "Defined",
        "temple": "Broad" if primary_shape in {"Heart", "Square"} else "Tapered",
    }

    return {
        "primary_shape": primary_shape,
        "width_to_length_ratio": round(width_to_length_ratio, 2),
        "jaw_ratio": round(jaw_ratio, 2),
        "forehead_ratio": round(forehead_ratio, 2),
        "shape_probabilities": shape_probabilities,
        "primary_percentage": round(top_probability, 2),
        "recommendations": _shape_recommendations(primary_shape),
        "characteristics": characteristics,
    }
