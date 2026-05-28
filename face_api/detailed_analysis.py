"""Detailed endpoint-specific analyses built on face landmarks and measurements."""

from __future__ import annotations

import math

from config import EYES_LEFT, EYES_RIGHT, GOLDEN_RATIO, IDEAL_PROPORTIONS, LIPS_L, LIPS_R, LIPS_TOP, NOSE_TIP
from features.eyes import analyze_eyes
from features.lips import analyze_lips
from features.nose import analyze_nose
from measurements import MeasurementResult, average_point
from scorer import clamp_score, score_from_ideal
from symmetry import compute_pair_score


def _difference_pct(left_value: float, right_value: float) -> float:
    """Return the percentage difference between left and right measurements."""

    return round((abs(left_value - right_value) / max(left_value, right_value, 1e-6)) * 100.0, 2)


def _detail_phrase(score: float) -> str:
    """Return a short verbal interpretation for a normalized score."""

    if score >= 90:
        return "very balanced"
    if score >= 75:
        return "well balanced"
    if score >= 60:
        return "moderately balanced"
    return "noticeably uneven"


def build_symmetry_report(
    measurements: MeasurementResult,
    pixel_landmarks: dict[int, tuple[float, float]],
) -> dict[str, object]:
    """Build a detailed symmetry report from paired and alignment measurements."""

    left_eye_center = average_point([pixel_landmarks[index] for index in EYES_LEFT])
    right_eye_center = average_point([pixel_landmarks[index] for index in EYES_RIGHT])
    eye_level_diff = abs(left_eye_center[1] - right_eye_center[1])
    eye_level_score = round(max(0.0, 100.0 - ((eye_level_diff / max(measurements.face_height, 1e-6)) * 500.0)), 2)

    mouth_corner_diff = measurements.lip_corner_diff
    mouth_level_score = round(max(0.0, 100.0 - ((mouth_corner_diff / max(measurements.mouth_width, 1e-6)) * 250.0)), 2)

    eye_mid_x = (left_eye_center[0] + right_eye_center[0]) / 2.0
    chin_x = pixel_landmarks[152][0]
    reference_midline_x = (eye_mid_x + chin_x) / 2.0
    nose_midline_offset = abs(pixel_landmarks[NOSE_TIP][0] - reference_midline_x)
    midline_score = round(max(0.0, 100.0 - ((nose_midline_offset / max(measurements.face_width, 1e-6)) * 400.0)), 2)

    paired_features = [
        {
            "feature": "Eye Width",
            "left_value": measurements.left_eye_width,
            "right_value": measurements.right_eye_width,
            "unit": "px",
            "difference_pct": _difference_pct(measurements.left_eye_width, measurements.right_eye_width),
            "score": compute_pair_score(measurements.left_eye_width, measurements.right_eye_width),
            "detail": "Compares the visible horizontal span of both eyes to show whether one eye reads larger in the frame.",
        },
        {
            "feature": "Eyebrow Length",
            "left_value": measurements.left_brow_length,
            "right_value": measurements.right_brow_length,
            "unit": "px",
            "difference_pct": _difference_pct(measurements.left_brow_length, measurements.right_brow_length),
            "score": compute_pair_score(measurements.left_brow_length, measurements.right_brow_length),
            "detail": "Looks at how similarly the brows stretch across the brow ridge, which affects perceived upper-face symmetry.",
        },
        {
            "feature": "Jaw Half Width",
            "left_value": measurements.jaw_half_width_left,
            "right_value": measurements.jaw_half_width_right,
            "unit": "px",
            "difference_pct": _difference_pct(measurements.jaw_half_width_left, measurements.jaw_half_width_right),
            "score": compute_pair_score(measurements.jaw_half_width_left, measurements.jaw_half_width_right),
            "detail": "Measures how evenly the jawline opens from the chin toward each side of the face.",
        },
    ]

    alignment_metrics = [
        {
            "name": "Eye Level Alignment",
            "value": round(eye_level_diff, 2),
            "unit": "px",
            "score": eye_level_score,
            "assessment": _detail_phrase(eye_level_score),
            "detail": "Smaller vertical eye-center difference means the face is sitting more level relative to the camera.",
        },
        {
            "name": "Mouth Corner Alignment",
            "value": round(mouth_corner_diff, 2),
            "unit": "px",
            "score": mouth_level_score,
            "assessment": _detail_phrase(mouth_level_score),
            "detail": "Compares left and right lip corner height to show whether the smile line or resting mouth is level.",
        },
        {
            "name": "Nose Midline Alignment",
            "value": round(nose_midline_offset, 2),
            "unit": "px",
            "score": midline_score,
            "assessment": _detail_phrase(midline_score),
            "detail": "Measures how closely the nose tip sits on the facial midline defined by the eye center and chin.",
        },
    ]

    all_scores = [item["score"] for item in paired_features] + [item["score"] for item in alignment_metrics]
    overall_score = round(sum(all_scores) / len(all_scores), 2)
    if overall_score >= 90:
        verdict = "Highly symmetric"
    elif overall_score >= 80:
        verdict = "Strong symmetry"
    elif overall_score >= 70:
        verdict = "Moderate symmetry"
    else:
        verdict = "Visible asymmetry"

    summary = (
        f"The face scores {overall_score} for symmetry overall. The strongest balance appears in the "
        f"{max(paired_features, key=lambda item: item['score'])['feature'].lower()}, while the most noticeable "
        f"imbalance shows up in the {min(alignment_metrics, key=lambda item: item['score'])['name'].lower()}."
    )
    return {
        "overall_score": overall_score,
        "verdict": verdict,
        "paired_features": paired_features,
        "alignment_metrics": alignment_metrics,
        "summary": summary,
    }


def build_eye_shape_report(
    measurements: MeasurementResult,
    pixel_landmarks: dict[int, tuple[float, float]],
) -> dict[str, object]:
    """Build a detailed eye-shape report from eye landmarks and measurements."""

    eye_analysis = analyze_eyes(measurements)
    left_tilt = math.degrees(math.atan2(pixel_landmarks[133][1] - pixel_landmarks[33][1], pixel_landmarks[133][0] - pixel_landmarks[33][0]))
    right_tilt = math.degrees(
        math.atan2(pixel_landmarks[263][1] - pixel_landmarks[362][1], pixel_landmarks[263][0] - pixel_landmarks[362][0])
    )
    mean_tilt = round((left_tilt + right_tilt) / 2.0, 2)
    openness_ratio = round(
        ((measurements.left_eye_height + measurements.right_eye_height) / 2.0)
        / max((measurements.left_eye_width + measurements.right_eye_width) / 2.0, 1e-6),
        3,
    )
    size_score = score_from_ideal(float(eye_analysis["mean_width"]) / max(measurements.face_width, 1e-6), 0.18, 60.0)
    spacing_score = score_from_ideal(float(eye_analysis["spacing_ratio"]), 0.30, 35.0)
    openness_score = score_from_ideal(openness_ratio, 0.38, 30.0)
    overall_score = round((size_score + spacing_score + openness_score + float(10.0 - float(eye_analysis["symmetry_difference_pct"]) * 0.12)) / 4.0, 2)

    if mean_tilt > 4:
        tilt_assessment = "Upturned"
    elif mean_tilt < -4:
        tilt_assessment = "Downturned"
    else:
        tilt_assessment = "Level"

    metrics = [
        {
            "name": "Average Eye Width",
            "measured": round(float(eye_analysis["mean_width"]), 2),
            "unit": "px",
            "ideal": round(measurements.face_width * 0.18, 2),
            "score": size_score,
            "assessment": eye_analysis["size"],
            "detail": "This compares the visible horizontal width of the eyes against total face width to judge whether the eyes read small, medium, or large.",
        },
        {
            "name": "Eye Openness Ratio",
            "measured": openness_ratio,
            "unit": "ratio",
            "ideal": 0.38,
            "score": openness_score,
            "assessment": "Open" if openness_ratio >= 0.38 else "Narrow",
            "detail": "A higher openness ratio means the eyelid opening is taller relative to eye width, which tends to read as more open and alert.",
        },
        {
            "name": "Eye Spacing Ratio",
            "measured": round(float(eye_analysis["spacing_ratio"]), 3),
            "unit": "ratio",
            "ideal": 0.30,
            "score": spacing_score,
            "assessment": eye_analysis["spacing"],
            "detail": "This ratio compares the space between the eyes to overall face width, which strongly affects whether the eyes look close-set or wide-set.",
        },
        {
            "name": "Canthal Tilt",
            "measured": mean_tilt,
            "unit": "degrees",
            "ideal": 0.0,
            "score": clamp_score(10.0 - abs(mean_tilt) * 0.6),
            "assessment": tilt_assessment,
            "detail": "Canthal tilt measures how much the outer eye corner sits above or below the inner corner in the photo.",
        },
    ]

    observations = [
        f"The primary eye shape reads as {eye_analysis['shape'].lower()} because the width-to-height ratio is {eye_analysis['aspect_ratio']}.",
        f"Eye spacing is classified as {eye_analysis['spacing'].lower()}, based on an interocular-to-face-width ratio of {eye_analysis['spacing_ratio']}.",
        f"Symmetry is {eye_analysis['symmetry'].lower()}, with a left-right eye width difference of {eye_analysis['symmetry_difference_pct']}%.",
    ]
    summary = (
        f"The eyes are classified as {eye_analysis['shape'].lower()} and {eye_analysis['size'].lower()}, "
        f"with a {tilt_assessment.lower()} canthal tilt and an overall eye-structure score of {overall_score}."
    )
    return {
        "primary_shape": eye_analysis["shape"],
        "size_classification": eye_analysis["size"],
        "spacing_classification": eye_analysis["spacing"],
        "symmetry_classification": eye_analysis["symmetry"],
        "overall_score": overall_score,
        "metrics": metrics,
        "observations": observations,
        "summary": summary,
    }


def build_lip_shape_report(
    measurements: MeasurementResult,
    pixel_landmarks: dict[int, tuple[float, float]],
) -> dict[str, object]:
    """Build a detailed lip-shape report from lip landmarks and measurements."""

    lip_analysis = analyze_lips(measurements)
    philtrum_length = round(abs(pixel_landmarks[NOSE_TIP][1] - pixel_landmarks[LIPS_TOP][1]), 2)
    corner_tilt = round(
        math.degrees(
            math.atan2(pixel_landmarks[LIPS_R][1] - pixel_landmarks[LIPS_L][1], pixel_landmarks[LIPS_R][0] - pixel_landmarks[LIPS_L][0])
        ),
        2,
    )
    fullness_score = score_from_ideal(float(lip_analysis["total_thickness"]), 20.0, 0.2)
    width_score = score_from_ideal(float(lip_analysis["width_ratio"]), 0.50, 40.0)
    balance_score = score_from_ideal(float(lip_analysis["upper_lower_ratio"]), 1.0, 6.0)
    overall_score = round((fullness_score + width_score + balance_score + float(10.0 - float(lip_analysis["symmetry_difference"]) * 0.4)) / 4.0, 2)

    metrics = [
        {
            "name": "Mouth Width Ratio",
            "measured": round(float(lip_analysis["width_ratio"]), 3),
            "unit": "ratio",
            "ideal": 0.50,
            "score": width_score,
            "assessment": lip_analysis["width"],
            "detail": "This measures how much of the face width is occupied by the mouth, which influences whether the lips read narrow, medium, or wide.",
        },
        {
            "name": "Total Lip Thickness",
            "measured": round(float(lip_analysis["total_thickness"]), 2),
            "unit": "px",
            "ideal": 20.0,
            "score": fullness_score,
            "assessment": lip_analysis["thickness"],
            "detail": "The combined upper and lower lip height gives a better sense of fullness than looking at the upper lip alone.",
        },
        {
            "name": "Upper-Lower Balance",
            "measured": round(float(lip_analysis["upper_lower_ratio"]), 3),
            "unit": "ratio",
            "ideal": 1.0,
            "score": balance_score,
            "assessment": lip_analysis["shape"],
            "detail": "This ratio shows whether the upper lip or lower lip is visually dominant, or whether both are close to balanced.",
        },
        {
            "name": "Philtrum Length",
            "measured": philtrum_length,
            "unit": "px",
            "ideal": None,
            "score": None,
            "assessment": "Compact" if philtrum_length < measurements.nose_length else "Extended",
            "detail": "Philtrum length influences how centrally the lips sit between the nose and chin and can change how full the lips appear.",
        },
        {
            "name": "Mouth Corner Tilt",
            "measured": corner_tilt,
            "unit": "degrees",
            "ideal": 0.0,
            "score": clamp_score(10.0 - abs(corner_tilt) * 0.7),
            "assessment": "Level" if abs(corner_tilt) < 3 else "Tilted",
            "detail": "Corner tilt shows whether one side of the mouth sits noticeably higher than the other in the captured frame.",
        },
    ]

    observations = [
        f"The lips read as {lip_analysis['thickness'].lower()} in fullness and {lip_analysis['shape'].lower()} in upper-to-lower balance.",
        f"The cupid bow is {lip_analysis['cupid_bow'].lower()}, based on a center offset of {lip_analysis['cupid_bow_offset']} px.",
        f"Lip symmetry is {lip_analysis['symmetry'].lower()}, with mouth corner height differing by {lip_analysis['symmetry_difference']} px.",
    ]
    summary = (
        f"The lips are classified as {lip_analysis['shape'].lower()} with {lip_analysis['thickness'].lower()} fullness "
        f"and a {lip_analysis['width'].lower()} mouth width, producing an overall lip harmony score of {overall_score}."
    )
    return {
        "primary_shape": lip_analysis["shape"],
        "width_classification": lip_analysis["width"],
        "thickness_classification": lip_analysis["thickness"],
        "symmetry_classification": lip_analysis["symmetry"],
        "overall_score": overall_score,
        "metrics": metrics,
        "observations": observations,
        "summary": summary,
    }


def build_nose_shape_report(
    measurements: MeasurementResult,
    pixel_landmarks: dict[int, tuple[float, float]],
) -> dict[str, object]:
    """Build a detailed nose-shape report from nose measurements."""

    nose_analysis = analyze_nose(measurements)
    nose_to_mouth_ratio = round(measurements.nose_width / max(measurements.mouth_width, 1e-6), 3)
    nose_to_face_center_offset = round(
        abs(pixel_landmarks[NOSE_TIP][0] - ((pixel_landmarks[234][0] + pixel_landmarks[454][0]) / 2.0)),
        2,
    )
    width_score = score_from_ideal(float(nose_analysis["width_ratio"]), 0.30, 40.0)
    length_score = score_from_ideal(float(nose_analysis["length_ratio"]), IDEAL_PROPORTIONS["nose_length_ratio"], 45.0)
    bridge_score = score_from_ideal(float(nose_analysis["bridge_ratio"]), 0.65, 18.0)
    overall_score = round((width_score + length_score + bridge_score) / 3.0, 2)

    metrics = [
        {
            "name": "Nose Width Ratio",
            "measured": round(float(nose_analysis["width_ratio"]), 3),
            "unit": "ratio",
            "ideal": 0.30,
            "score": width_score,
            "assessment": nose_analysis["width"],
            "detail": "This compares nostril span against overall face width to show how broad the nose reads in the face.",
        },
        {
            "name": "Nose Length Ratio",
            "measured": round(float(nose_analysis["length_ratio"]), 3),
            "unit": "ratio",
            "ideal": IDEAL_PROPORTIONS["nose_length_ratio"],
            "score": length_score,
            "assessment": nose_analysis["length"],
            "detail": "This reflects how much vertical face height the nose occupies from bridge to tip.",
        },
        {
            "name": "Bridge Height Ratio",
            "measured": round(float(nose_analysis["bridge_ratio"]), 3),
            "unit": "ratio",
            "ideal": 0.65,
            "score": bridge_score,
            "assessment": nose_analysis["bridge"],
            "detail": "Bridge height ratio helps distinguish flatter bridges from more projected bridges in a frontal image.",
        },
        {
            "name": "Nose-to-Mouth Width Ratio",
            "measured": nose_to_mouth_ratio,
            "unit": "ratio",
            "ideal": 0.6,
            "score": score_from_ideal(nose_to_mouth_ratio, 0.6, 10.0),
            "assessment": "Balanced" if 0.5 <= nose_to_mouth_ratio <= 0.7 else "Distinctive",
            "detail": "This compares the width of the nose to the width of the mouth to evaluate central facial balance.",
        },
        {
            "name": "Nose Midline Offset",
            "measured": nose_to_face_center_offset,
            "unit": "px",
            "ideal": 0.0,
            "score": clamp_score(10.0 - (nose_to_face_center_offset / max(measurements.face_width, 1e-6)) * 60.0),
            "assessment": "Centered" if nose_to_face_center_offset <= measurements.face_width * 0.02 else "Shifted",
            "detail": "A smaller offset means the nose tip sits more centrally between the two sides of the face.",
        },
    ]

    observations = [
        f"The primary nose shape is classified as {nose_analysis['shape'].lower()} because the bridge is {nose_analysis['bridge'].lower()} and the width is {nose_analysis['width'].lower()}.",
        f"Nasal proportion is described as {nose_analysis['proportion'].lower()}, based on width ratio {nose_analysis['width_ratio']} and length ratio {nose_analysis['length_ratio']}.",
        f"The bridge is classified as {nose_analysis['bridge'].lower()} with a bridge-height ratio of {nose_analysis['bridge_ratio']}.",
    ]
    summary = (
        f"The nose reads as a {nose_analysis['shape'].lower()} shape with {nose_analysis['width'].lower()} width, "
        f"{nose_analysis['length'].lower()} length, and an overall nasal proportion score of {overall_score}."
    )
    return {
        "primary_shape": nose_analysis["shape"],
        "width_classification": nose_analysis["width"],
        "length_classification": nose_analysis["length"],
        "bridge_classification": nose_analysis["bridge"],
        "overall_score": overall_score,
        "metrics": metrics,
        "observations": observations,
        "summary": summary,
    }


def build_golden_ratio_report(measurements: MeasurementResult) -> dict[str, object]:
    """Build a detailed golden-ratio report from canon-based face measurements."""

    components = [
        {
            "name": "Face Width to Height",
            "measured": round(measurements.face_width / max(measurements.face_height, 1e-6), 3),
            "ideal": IDEAL_PROPORTIONS["face_ratio"],
            "score": score_from_ideal(measurements.face_width / max(measurements.face_height, 1e-6), IDEAL_PROPORTIONS["face_ratio"], 15.0),
            "weight": 0.25,
            "detail": "This is the broad structural ratio of the face and strongly influences whether the face feels balanced or elongated.",
        },
        {
            "name": "Eye Spacing Ratio",
            "measured": round(measurements.interocular_distance / max(measurements.face_width, 1e-6), 3),
            "ideal": IDEAL_PROPORTIONS["eye_spacing_ratio"],
            "score": score_from_ideal(measurements.interocular_distance / max(measurements.face_width, 1e-6), IDEAL_PROPORTIONS["eye_spacing_ratio"], 30.0),
            "weight": 0.25,
            "detail": "This compares the distance between the eyes to face width, one of the most noticeable harmony markers in frontal portraits.",
        },
        {
            "name": "Nose Length Ratio",
            "measured": round(measurements.nose_length / max(measurements.face_height, 1e-6), 3),
            "ideal": IDEAL_PROPORTIONS["nose_length_ratio"],
            "score": score_from_ideal(measurements.nose_length / max(measurements.face_height, 1e-6), IDEAL_PROPORTIONS["nose_length_ratio"], 45.0),
            "weight": 0.20,
            "detail": "Nose length is compared to total face height to estimate whether the nose occupies a harmonious vertical share of the face.",
        },
        {
            "name": "Mouth Width Ratio",
            "measured": round(measurements.mouth_width / max(measurements.face_width, 1e-6), 3),
            "ideal": IDEAL_PROPORTIONS["mouth_width_ratio"],
            "score": score_from_ideal(measurements.mouth_width / max(measurements.face_width, 1e-6), IDEAL_PROPORTIONS["mouth_width_ratio"], 40.0),
            "weight": 0.20,
            "detail": "This compares mouth width to total face width to see whether the mouth visually supports the middle and lower face proportionally.",
        },
        {
            "name": "Face Height to Width vs Phi",
            "measured": round(measurements.face_height / max(measurements.face_width, 1e-6), 3),
            "ideal": GOLDEN_RATIO,
            "score": score_from_ideal(measurements.face_height / max(measurements.face_width, 1e-6), GOLDEN_RATIO, 8.0),
            "weight": 0.10,
            "detail": "This compares the face's vertical-to-horizontal proportion with the classical golden-ratio target often referenced in portrait analysis.",
        },
    ]

    weighted_score = sum(component["score"] * component["weight"] for component in components)
    overall_score = round(weighted_score * 10.0, 2)
    strongest_components = [component["name"] for component in sorted(components, key=lambda item: item["score"], reverse=True)[:2]]
    improvement_areas = [component["name"] for component in sorted(components, key=lambda item: item["score"])[:2]]
    summary = (
        f"The face scores {overall_score} out of 100 on this golden-ratio breakdown. "
        f"The strongest harmony appears in {strongest_components[0].lower()}, while the largest deviation appears in {improvement_areas[0].lower()}."
    )
    return {
        "overall_score": overall_score,
        "components": components,
        "strongest_components": strongest_components,
        "improvement_areas": improvement_areas,
        "summary": summary,
    }
