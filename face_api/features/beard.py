"""Beard detection and heuristic classification."""

from __future__ import annotations

import cv2
import numpy as np

from config import JAW, LIPS_BOT, LIPS_L, LIPS_R, LIPS_TOP, NOSE_TIP


def _clamp_box(value: int, minimum: int, maximum: int) -> int:
    """Clamp a bounding-box coordinate into the image bounds."""

    return max(minimum, min(value, maximum))


def _extract_roi(
    image_bgr: np.ndarray,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> np.ndarray:
    """Extract a bounded ROI from the image."""

    height, width = image_bgr.shape[:2]
    safe_left = _clamp_box(left, 0, width)
    safe_right = _clamp_box(right, 0, width)
    safe_top = _clamp_box(top, 0, height)
    safe_bottom = _clamp_box(bottom, 0, height)
    if safe_right <= safe_left or safe_bottom <= safe_top:
        return np.empty((0, 0, 3), dtype=image_bgr.dtype)
    return image_bgr[safe_top:safe_bottom, safe_left:safe_right]


def _compute_region_metrics(region_bgr: np.ndarray) -> dict[str, float]:
    """Compute grayscale intensity, edge density, texture variation, and dark ratio for a region."""

    if region_bgr.size == 0:
        return {
            "avg_intensity": 0.0,
            "edge_density": 0.0,
            "texture_variation": 0.0,
            "dark_ratio": 0.0,
        }

    gray = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    return {
        "avg_intensity": float(gray.mean()),
        "edge_density": float(np.count_nonzero(edges) / max(edges.size, 1)),
        "texture_variation": float(gray.std()),
        "dark_ratio": float(np.count_nonzero(gray < 110) / max(gray.size, 1)),
    }


def _unknown_beard_response(metrics: dict[str, float], mustache_score: float) -> dict[str, float | str | bool | dict[str, float]]:
    """Build the standard non-detected beard payload."""

    return {
        "detected": False,
        "style": "Unknown",
        "density": "Unknown",
        "coverage": "Unknown",
        "avg_intensity": round(metrics["avg_intensity"], 2),
        "edge_density": round(metrics["edge_density"], 4),
        "texture_variation": round(metrics["texture_variation"], 2),
        "mustache_score": round(mustache_score, 2),
        "ratings": {"density": 0.0, "style": 0.0, "overall": 0.0},
    }


def _score_detected_beard(density: str, style: str) -> dict[str, float]:
    """Map beard classifications to numeric ratings."""

    density_scores = {"Light": 5.5, "Medium": 7.5, "Full": 9.0}
    style_scores = {"Stubble": 6.5, "Goatee": 7.5, "Mustache": 7.0, "Full Beard": 9.0}
    density_score = density_scores.get(density, 0.0)
    style_score = style_scores.get(style, 0.0)
    overall = round((density_score + style_score) / 2.0, 1)
    return {
        "density": round(density_score, 1),
        "style": round(style_score, 1),
        "overall": overall,
    }


def analyze_beard(
    image_bgr: np.ndarray,
    pixel_landmarks: dict[int, tuple[float, float]],
) -> dict[str, float | str | bool | dict[str, float]]:
    """Detect beard presence and classify beard style, density, and coverage."""

    height, width = image_bgr.shape[:2]
    jaw_points = np.array([pixel_landmarks[index] for index in JAW], dtype=float)
    beard_roi = _extract_roi(
        image_bgr,
        left=int(jaw_points[:, 0].min()) + 6,
        top=int(pixel_landmarks[LIPS_BOT][1]) + 4,
        right=int(jaw_points[:, 0].max()) - 6,
        bottom=int(jaw_points[:, 1].max()) + 8,
    )
    beard_metrics = _compute_region_metrics(beard_roi)
    if beard_roi.size == 0:
        return _unknown_beard_response(beard_metrics, 0.0)

    mustache_left = int(min(pixel_landmarks[LIPS_L][0], pixel_landmarks[LIPS_R][0]))
    mustache_right = int(max(pixel_landmarks[LIPS_L][0], pixel_landmarks[LIPS_R][0]))
    mustache_top = _clamp_box(int(min(pixel_landmarks[NOSE_TIP][1], pixel_landmarks[LIPS_TOP][1])) - 6, 0, height)
    mustache_bottom = _clamp_box(int(max(pixel_landmarks[NOSE_TIP][1], pixel_landmarks[LIPS_TOP][1])) + 6, 0, height)
    mustache_roi = _extract_roi(image_bgr, mustache_left, mustache_top, mustache_right, mustache_bottom)
    mustache_metrics = _compute_region_metrics(mustache_roi)

    cheek_top = int(min(pixel_landmarks[NOSE_TIP][1], pixel_landmarks[LIPS_TOP][1]))
    cheek_bottom = int(max(pixel_landmarks[LIPS_TOP][1], pixel_landmarks[LIPS_BOT][1]))
    left_outer = int(pixel_landmarks[234][0])
    left_inner = int(pixel_landmarks[LIPS_L][0])
    right_inner = int(pixel_landmarks[LIPS_R][0])
    right_outer = int(pixel_landmarks[454][0])

    left_cheek_roi = _extract_roi(
        image_bgr,
        left=int(left_outer + (left_inner - left_outer) * 0.20),
        top=cheek_top,
        right=int(left_outer + (left_inner - left_outer) * 0.75),
        bottom=cheek_bottom,
    )
    right_cheek_roi = _extract_roi(
        image_bgr,
        left=int(right_inner + (right_outer - right_inner) * 0.25),
        top=cheek_top,
        right=int(right_inner + (right_outer - right_inner) * 0.80),
        bottom=cheek_bottom,
    )
    left_cheek_metrics = _compute_region_metrics(left_cheek_roi)
    right_cheek_metrics = _compute_region_metrics(right_cheek_roi)
    cheek_intensity = (left_cheek_metrics["avg_intensity"] + right_cheek_metrics["avg_intensity"]) / 2.0
    cheek_edge_density = (left_cheek_metrics["edge_density"] + right_cheek_metrics["edge_density"]) / 2.0
    cheek_texture = (left_cheek_metrics["texture_variation"] + right_cheek_metrics["texture_variation"]) / 2.0

    mustache_score = float((mustache_metrics["edge_density"] * 100.0) + (mustache_metrics["texture_variation"] / 2.0))
    beard_darkness_delta = cheek_intensity - beard_metrics["avg_intensity"]
    beard_texture_delta = beard_metrics["texture_variation"] - cheek_texture
    beard_edge_delta = beard_metrics["edge_density"] - cheek_edge_density
    mustache_darkness_delta = cheek_intensity - mustache_metrics["avg_intensity"]

    detected = (
        beard_metrics["edge_density"] > 0.10
        and beard_metrics["texture_variation"] > 18
        and beard_metrics["dark_ratio"] > 0.18
        and beard_darkness_delta > 10
        and beard_texture_delta > 3
        and beard_edge_delta > 0.015
    ) or (
        mustache_metrics["edge_density"] > 0.12
        and mustache_metrics["texture_variation"] > 18
        and mustache_darkness_delta > 12
        and beard_metrics["edge_density"] > 0.08
        and beard_darkness_delta > 8
    )
    if not detected:
        return _unknown_beard_response(beard_metrics, mustache_score)

    if beard_metrics["edge_density"] > 0.16 or beard_metrics["texture_variation"] > 35:
        density = "Full"
    elif beard_metrics["edge_density"] > 0.12 or beard_metrics["texture_variation"] > 24:
        density = "Medium"
    else:
        density = "Light"

    if beard_metrics["dark_ratio"] > 0.45:
        coverage = "Full"
    elif beard_metrics["dark_ratio"] > 0.25:
        coverage = "Partial"
    else:
        coverage = "Minimal"

    if mustache_score > 24 and coverage == "Minimal":
        style = "Mustache"
    elif coverage == "Full" and density == "Full":
        style = "Full Beard"
    elif coverage == "Partial":
        style = "Goatee"
    else:
        style = "Stubble"

    return {
        "detected": True,
        "style": style,
        "density": density,
        "coverage": coverage,
        "avg_intensity": round(beard_metrics["avg_intensity"], 2),
        "edge_density": round(beard_metrics["edge_density"], 4),
        "texture_variation": round(beard_metrics["texture_variation"], 2),
        "mustache_score": round(mustache_score, 2),
        "ratings": _score_detected_beard(density, style),
    }
