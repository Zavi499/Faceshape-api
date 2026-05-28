"""Geometric measurement helpers built on facial landmarks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import (
    BROW_LEFT,
    BROW_RIGHT,
    EYES_LEFT,
    EYES_RIGHT,
    FOREHEAD,
    JAW,
    LIPS_BOT,
    LIPS_L,
    LIPS_R,
    LIPS_TOP,
    NOSE_BRIDGE,
    NOSE_L,
    NOSE_R,
    NOSE_TIP,
)

Point = tuple[float, float]


def to_pixel_landmarks(face_landmarks, image_width: int, image_height: int) -> dict[int, Point]:
    """Convert normalized MediaPipe landmarks to pixel coordinates."""

    landmark_iterable = face_landmarks.landmark if hasattr(face_landmarks, "landmark") else face_landmarks
    return {
        index: (
            landmark.x * image_width,
            landmark.y * image_height,
        )
        for index, landmark in enumerate(landmark_iterable)
    }


def euclidean_distance(point_a: Point, point_b: Point) -> float:
    """Return the Euclidean distance between two 2D points."""

    return float(np.linalg.norm(np.array(point_a, dtype=float) - np.array(point_b, dtype=float)))


def midpoint(point_a: Point, point_b: Point) -> Point:
    """Return the midpoint between two 2D points."""

    return ((point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0)


def average_point(points: list[Point]) -> Point:
    """Return the arithmetic mean of a list of points."""

    array = np.array(points, dtype=float)
    return (float(array[:, 0].mean()), float(array[:, 1].mean()))


def _round(value: float) -> float:
    """Round measurement values to two decimal places."""

    return round(float(value), 2)


@dataclass(slots=True)
class MeasurementResult:
    """Full set of public and support measurements derived from landmarks."""

    face_width: float
    face_height: float
    eye_span: float
    interocular_distance: float
    forehead_width: float
    jaw_width: float
    mouth_width: float
    nose_length: float
    nose_width: float
    left_eye_width: float
    right_eye_width: float
    left_eye_height: float
    right_eye_height: float
    left_brow_length: float
    right_brow_length: float
    left_brow_height: float
    right_brow_height: float
    brow_gap: float
    upper_lip_height: float
    lower_lip_height: float
    upper_to_lower_ratio: float
    cupid_bow_offset: float
    lip_corner_diff: float
    bridge_height: float
    cheekbone_width: float
    jaw_half_width_left: float
    jaw_half_width_right: float

    def to_response_dict(self) -> dict[str, float]:
        """Return the public measurement fields used in the API response."""

        return {
            "face_width": self.face_width,
            "face_height": self.face_height,
            "eye_span": self.eye_span,
            "interocular_distance": self.interocular_distance,
            "forehead_width": self.forehead_width,
            "jaw_width": self.jaw_width,
            "mouth_width": self.mouth_width,
            "nose_length": self.nose_length,
            "nose_width": self.nose_width,
        }


def compute_measurements(pixel_landmarks: dict[int, Point]) -> MeasurementResult:
    """Compute the core and support facial measurements from pixel landmarks."""

    left_eye_center = average_point([pixel_landmarks[index] for index in EYES_LEFT])
    right_eye_center = average_point([pixel_landmarks[index] for index in EYES_RIGHT])
    nose_side_midpoint = midpoint(pixel_landmarks[NOSE_L], pixel_landmarks[NOSE_R])

    left_eye_width = euclidean_distance(pixel_landmarks[33], pixel_landmarks[133])
    right_eye_width = euclidean_distance(pixel_landmarks[362], pixel_landmarks[263])
    left_eye_height = (
        euclidean_distance(pixel_landmarks[160], pixel_landmarks[144])
        + euclidean_distance(pixel_landmarks[158], pixel_landmarks[153])
    ) / 2.0
    right_eye_height = (
        euclidean_distance(pixel_landmarks[385], pixel_landmarks[380])
        + euclidean_distance(pixel_landmarks[387], pixel_landmarks[373])
    ) / 2.0

    mouth_line_y = (pixel_landmarks[LIPS_L][1] + pixel_landmarks[LIPS_R][1]) / 2.0
    upper_lip_height = abs(mouth_line_y - pixel_landmarks[LIPS_TOP][1])
    lower_lip_height = abs(pixel_landmarks[LIPS_BOT][1] - mouth_line_y)
    upper_to_lower_ratio = upper_lip_height / max(lower_lip_height, 1e-6)
    cupid_bow_offset = abs(mouth_line_y - pixel_landmarks[LIPS_TOP][1])
    lip_corner_diff = abs(pixel_landmarks[LIPS_L][1] - pixel_landmarks[LIPS_R][1])

    left_brow_length = euclidean_distance(pixel_landmarks[BROW_LEFT[0]], pixel_landmarks[BROW_LEFT[-1]])
    right_brow_length = euclidean_distance(pixel_landmarks[BROW_RIGHT[0]], pixel_landmarks[BROW_RIGHT[-1]])
    left_brow_height = max(pixel_landmarks[index][1] for index in BROW_LEFT) - min(
        pixel_landmarks[index][1] for index in BROW_LEFT
    )
    right_brow_height = max(pixel_landmarks[index][1] for index in BROW_RIGHT) - min(
        pixel_landmarks[index][1] for index in BROW_RIGHT
    )

    return MeasurementResult(
        face_width=_round(euclidean_distance(pixel_landmarks[234], pixel_landmarks[454])),
        face_height=_round(euclidean_distance(pixel_landmarks[10], pixel_landmarks[152])),
        eye_span=_round(euclidean_distance(pixel_landmarks[33], pixel_landmarks[263])),
        interocular_distance=_round(euclidean_distance(left_eye_center, right_eye_center)),
        forehead_width=_round(euclidean_distance(pixel_landmarks[FOREHEAD[1]], pixel_landmarks[FOREHEAD[-1]])),
        jaw_width=_round(euclidean_distance(pixel_landmarks[JAW[1]], pixel_landmarks[JAW[3]])),
        mouth_width=_round(euclidean_distance(pixel_landmarks[LIPS_L], pixel_landmarks[LIPS_R])),
        nose_length=_round(euclidean_distance(pixel_landmarks[NOSE_BRIDGE], pixel_landmarks[NOSE_TIP])),
        nose_width=_round(euclidean_distance(pixel_landmarks[NOSE_L], pixel_landmarks[NOSE_R])),
        left_eye_width=_round(left_eye_width),
        right_eye_width=_round(right_eye_width),
        left_eye_height=_round(left_eye_height),
        right_eye_height=_round(right_eye_height),
        left_brow_length=_round(left_brow_length),
        right_brow_length=_round(right_brow_length),
        left_brow_height=_round(left_brow_height),
        right_brow_height=_round(right_brow_height),
        brow_gap=_round(euclidean_distance(pixel_landmarks[BROW_LEFT[-1]], pixel_landmarks[BROW_RIGHT[0]])),
        upper_lip_height=_round(upper_lip_height),
        lower_lip_height=_round(lower_lip_height),
        upper_to_lower_ratio=_round(upper_to_lower_ratio),
        cupid_bow_offset=_round(cupid_bow_offset),
        lip_corner_diff=_round(lip_corner_diff),
        bridge_height=_round(euclidean_distance(pixel_landmarks[NOSE_BRIDGE], nose_side_midpoint)),
        cheekbone_width=_round(euclidean_distance(pixel_landmarks[234], pixel_landmarks[454])),
        jaw_half_width_left=_round(euclidean_distance(pixel_landmarks[234], pixel_landmarks[152])),
        jaw_half_width_right=_round(euclidean_distance(pixel_landmarks[454], pixel_landmarks[152])),
    )
