"""Feature scoring and overall attractiveness rating."""

from __future__ import annotations

from config import FEATURE_WEIGHTS, GOLDEN_RATIO, IDEAL_PROPORTIONS
from measurements import MeasurementResult


def clamp_score(value: float) -> float:
    """Clamp a numeric score into the allowed 0.0 to 10.0 range."""

    return round(min(max(value, 0.0), 10.0), 1)


def score_from_ideal(measured: float, ideal: float, penalty: float) -> float:
    """Score a measured value against its ideal target using the shared formula."""

    return clamp_score(10.0 - abs(measured - ideal) * penalty)


def _rating_message(percentage: float) -> str:
    """Return the user-facing rating message for an overall percentage."""

    if percentage >= 90:
        return "You are exceptionally attractive!"
    if percentage >= 80:
        return "You are very attractive!"
    if percentage >= 70:
        return "You are above average in attractiveness!"
    if percentage >= 60:
        return "You are attractive!"
    return "You have unique and interesting features!"


def calculate_scores(
    measurements: MeasurementResult,
    eyes: dict[str, float | str],
    eyebrows: dict[str, float | str],
    nose: dict[str, float | str],
    lips: dict[str, float | str],
    face_shape: dict[str, float | str | dict | list[str]],
) -> dict[str, dict | float | str]:
    """Calculate per-feature ratings, golden-ratio score, and overall rating."""

    eye_spacing_score = score_from_ideal(
        measurements.interocular_distance / max(measurements.face_width, 1e-6),
        IDEAL_PROPORTIONS["eye_spacing_ratio"],
        30.0,
    )
    eye_size_score = score_from_ideal(
        ((measurements.left_eye_width + measurements.right_eye_width) / 2.0) / max(measurements.face_width, 1e-6),
        0.18,
        60.0,
    )
    eye_shape_score = score_from_ideal(float(eyes["aspect_ratio"]), 2.0, 3.0)
    eye_symmetry_score = clamp_score(10.0 - (float(eyes["symmetry_difference_pct"]) * 0.12))
    eye_overall = clamp_score((eye_spacing_score + eye_size_score + eye_shape_score + eye_symmetry_score) / 4.0)

    brow_arch_score = score_from_ideal(float(eyebrows["arch_delta"]), 4.0, 1.2)
    brow_spacing_score = score_from_ideal(float(eyebrows["spacing_ratio"]), 0.15, 35.0)
    brow_thickness_score = score_from_ideal(float(eyebrows["average_height"]), 12.0, 0.5)
    brow_overall = clamp_score((brow_arch_score + brow_spacing_score + brow_thickness_score) / 3.0)

    nose_width_score = score_from_ideal(float(nose["width_ratio"]), 0.30, 40.0)
    nose_length_score = score_from_ideal(float(nose["length_ratio"]), IDEAL_PROPORTIONS["nose_length_ratio"], 45.0)
    nose_bridge_score = score_from_ideal(float(nose["bridge_ratio"]), 0.65, 18.0)
    nose_proportion_score = clamp_score((nose_width_score + nose_length_score) / 2.0)
    nose_overall = clamp_score((nose_width_score + nose_length_score + nose_bridge_score + nose_proportion_score) / 4.0)

    lip_shape_score = score_from_ideal(float(lips["upper_lower_ratio"]), 1.0, 6.0)
    lip_thickness_score = score_from_ideal(float(lips["total_thickness"]), 20.0, 0.2)
    lip_width_score = score_from_ideal(float(lips["width_ratio"]), IDEAL_PROPORTIONS["mouth_width_ratio"], 40.0)
    cupid_bow_score = score_from_ideal(float(lips["cupid_bow_offset"]), 6.0, 0.8)
    lip_proportion_score = clamp_score((lip_width_score + lip_shape_score) / 2.0)
    lip_overall = clamp_score(
        (lip_shape_score + lip_thickness_score + lip_width_score + cupid_bow_score + lip_proportion_score) / 5.0
    )

    face_ratio = measurements.face_width / max(measurements.face_height, 1e-6)
    face_ratio_score = score_from_ideal(face_ratio, IDEAL_PROPORTIONS["face_ratio"], 15.0)
    face_shape_confidence_score = clamp_score(float(face_shape["primary_percentage"]) / 10.0)
    face_shape_overall = clamp_score((face_ratio_score + face_shape_confidence_score) / 2.0)

    feature_scores = {
        "eyes": eye_overall,
        "nose": nose_overall,
        "lips": lip_overall,
        "eyebrows": brow_overall,
        "face_shape": face_shape_overall,
    }
    overall_rating = sum(feature_scores[name] * FEATURE_WEIGHTS[name] for name in FEATURE_WEIGHTS)
    overall_rating = clamp_score(overall_rating)
    percentage = round(overall_rating * 10.0, 1)

    facial_ratio = measurements.face_height / max(measurements.face_width, 1e-6)
    golden_ratio_score = score_from_ideal(facial_ratio, GOLDEN_RATIO, 8.0)

    ratings = {
        "eyes": {
            "shape": eye_shape_score,
            "size": eye_size_score,
            "spacing": eye_spacing_score,
            "symmetry": eye_symmetry_score,
            "overall": eye_overall,
        },
        "eyebrows": {
            "arch": brow_arch_score,
            "spacing": brow_spacing_score,
            "thickness": brow_thickness_score,
            "overall": brow_overall,
        },
        "nose": {
            "width": nose_width_score,
            "length": nose_length_score,
            "bridge": nose_bridge_score,
            "proportion": nose_proportion_score,
            "overall": nose_overall,
        },
        "lips": {
            "shape": lip_shape_score,
            "thickness": lip_thickness_score,
            "width": lip_width_score,
            "cupid_bow": cupid_bow_score,
            "proportion": lip_proportion_score,
            "overall": lip_overall,
        },
        "face_shape": {
            "overall": face_shape_overall,
        },
    }

    return {
        "ratings": ratings,
        "feature_scores": feature_scores,
        "golden_ratio_score": golden_ratio_score,
        "overall_rating": overall_rating,
        "percentage": percentage,
        "rating_message": _rating_message(percentage),
    }
