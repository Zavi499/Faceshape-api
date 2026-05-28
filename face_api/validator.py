"""Upload validation and image quality assessment utilities."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import cv2
import numpy as np
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from config import ALLOWED_TYPES, MAX_FILE_SIZE_MB, MIN_RESOLUTION, NOSE_TIP


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation checks."""

    def __init__(self, message: str, detail: str) -> None:
        """Store a user-safe message and a more specific detail string."""

        super().__init__(detail)
        self.message = message
        self.detail = detail


@dataclass(slots=True)
class ValidatedImage:
    """Validated image payload ready for further analysis."""

    pil_image: Image.Image
    bgr_image: np.ndarray
    width: int
    height: int
    mime_type: str
    size_bytes: int


def validate_upload_file(upload_file: UploadFile, content: bytes) -> ValidatedImage:
    """Validate uploaded image type, size, and minimum resolution."""

    if upload_file.content_type not in ALLOWED_TYPES:
        raise FileValidationError(
            "Invalid file type.",
            "Only JPEG, PNG, and WEBP images are supported.",
        )

    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size_bytes:
        raise FileValidationError(
            "File too large.",
            f"Image size must be less than or equal to {MAX_FILE_SIZE_MB} MB.",
        )

    try:
        pil_image = Image.open(BytesIO(content)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise FileValidationError(
            "Invalid image file.",
            "The uploaded file could not be decoded as a valid image.",
        ) from exc

    width, height = pil_image.size
    min_width, min_height = MIN_RESOLUTION
    if width < min_width or height < min_height:
        raise FileValidationError(
            "Image resolution too small.",
            f"Minimum allowed resolution is {min_width}x{min_height} pixels.",
        )

    rgb_array = np.array(pil_image)
    bgr_image = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    return ValidatedImage(
        pil_image=pil_image,
        bgr_image=bgr_image,
        width=width,
        height=height,
        mime_type=upload_file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )


def analyze_image_quality(
    image_bgr: np.ndarray,
    pixel_landmarks: dict[int, tuple[float, float]],
) -> dict[str, float | str | None]:
    """Compute lighting, blur, face angle, and overall quality guidance."""

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    mean_intensity = float(gray.mean())
    if mean_intensity < 60:
        lighting = "dark"
        lighting_score = 40.0
    elif mean_intensity > 200:
        lighting = "overexposed"
        lighting_score = 35.0
    else:
        lighting = "good"
        lighting_score = 100.0

    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_score = min(blur_variance / 5.0, 100.0)

    left_eye = np.array(pixel_landmarks[33], dtype=float)
    right_eye = np.array(pixel_landmarks[263], dtype=float)
    nose_tip = np.array(pixel_landmarks[NOSE_TIP], dtype=float)
    eye_midpoint = (left_eye + right_eye) / 2.0
    half_eye_distance = max(np.linalg.norm(right_eye - left_eye) / 2.0, 1e-6)
    yaw_degrees = float(np.degrees(np.arctan2(abs(nose_tip[0] - eye_midpoint[0]), half_eye_distance)))

    if yaw_degrees < 10:
        face_angle = "frontal"
        angle_score = 100.0
    elif yaw_degrees <= 25:
        face_angle = "slightly_angled"
        angle_score = 75.0
    else:
        face_angle = "angled"
        angle_score = 45.0

    quality_score = (lighting_score * 0.4) + (blur_score * 0.4) + (angle_score * 0.2)
    quality_score = round(min(quality_score, 100.0), 2)
    recommendation = None
    if quality_score < 60:
        recommendation = "Try a straight-on photo in better lighting"

    return {
        "lighting": lighting,
        "face_angle": face_angle,
        "blur_score": round(blur_score, 2),
        "quality_score": quality_score,
        "recommendation": recommendation,
    }
