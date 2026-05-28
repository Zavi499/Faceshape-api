"""Dedicated age estimation model integration."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

import cv2
import numpy as np

from config import (
    AGE_BUCKET_CENTERS,
    AGE_BUCKETS,
    AGE_MODEL_INPUT_SIZE,
    AGE_MODEL_MEAN_VALUES,
    AGE_MODEL_PROTO_PATH,
    AGE_MODEL_PROTO_URL,
    AGE_MODEL_WEIGHTS_PATH,
    AGE_MODEL_WEIGHTS_URL,
    ensure_models_dir,
)


class AgeEstimator:
    """Lazy wrapper around a dedicated DNN age-estimation model."""

    def __init__(self) -> None:
        """Initialize the age estimator and load model files."""

        proto_path, weights_path = self._ensure_model_files()
        self._net = cv2.dnn.readNetFromCaffe(str(proto_path), str(weights_path))

    @staticmethod
    def _download_file(url: str, destination: Path) -> Path:
        """Download a file to the destination path if it does not already exist."""

        if destination.exists():
            return destination

        ensure_models_dir()
        with urlopen(url, timeout=120) as response:
            destination.write_bytes(response.read())
        return destination

    @classmethod
    def _ensure_model_files(cls) -> tuple[Path, Path]:
        """Ensure the age model files are present locally."""

        proto_path = cls._download_file(AGE_MODEL_PROTO_URL, AGE_MODEL_PROTO_PATH)
        weights_path = cls._download_file(AGE_MODEL_WEIGHTS_URL, AGE_MODEL_WEIGHTS_PATH)
        return proto_path, weights_path

    @staticmethod
    def _extract_face_crop(
        image_bgr: np.ndarray,
        pixel_landmarks: dict[int, tuple[float, float]],
    ) -> np.ndarray:
        """Crop a padded face region from landmarks for age inference."""

        height, width = image_bgr.shape[:2]
        coordinates = np.array(list(pixel_landmarks.values()), dtype=float)
        min_x = max(int(coordinates[:, 0].min()) - 20, 0)
        max_x = min(int(coordinates[:, 0].max()) + 20, width)
        min_y = max(int(coordinates[:, 1].min()) - 30, 0)
        max_y = min(int(coordinates[:, 1].max()) + 20, height)
        if max_x <= min_x or max_y <= min_y:
            return np.empty((0, 0, 3), dtype=image_bgr.dtype)
        return image_bgr[min_y:max_y, min_x:max_x]

    def estimate(
        self,
        image_bgr: np.ndarray,
        pixel_landmarks: dict[int, tuple[float, float]],
    ) -> dict[str, object]:
        """Estimate age distribution, dominant bucket, and weighted average age."""

        face_crop = self._extract_face_crop(image_bgr, pixel_landmarks)
        if face_crop.size == 0:
            raise ValueError("Unable to isolate a valid face crop for age estimation.")

        blob = cv2.dnn.blobFromImage(
            image=face_crop,
            scalefactor=1.0,
            size=AGE_MODEL_INPUT_SIZE,
            mean=AGE_MODEL_MEAN_VALUES,
            swapRB=False,
            crop=False,
        )
        self._net.setInput(blob)
        predictions = self._net.forward().flatten()
        probabilities = predictions / max(float(predictions.sum()), 1e-6)

        weighted_age = sum(center * probability for center, probability in zip(AGE_BUCKET_CENTERS, probabilities))
        top_indices = np.argsort(probabilities)[::-1][:3]
        confidence_ranking = [
            {
                "range": AGE_BUCKETS[index],
                "confidence": round(float(probabilities[index] * 100.0), 2),
            }
            for index in top_indices
        ]
        dominant_index = int(np.argmax(probabilities))
        dominant_confidence = float(probabilities[dominant_index] * 100.0)

        if dominant_confidence >= 60:
            reliability = "high"
        elif dominant_confidence >= 40:
            reliability = "medium"
        else:
            reliability = "low"

        return {
            "model_name": "Levi-Hassner AgeNet (Caffe)",
            "predicted_age_range": AGE_BUCKETS[dominant_index],
            "estimated_age": round(float(weighted_age), 1),
            "confidence": round(dominant_confidence, 2),
            "reliability": reliability,
            "top_predictions": confidence_ranking,
            "face_crop_size": {
                "width": int(face_crop.shape[1]),
                "height": int(face_crop.shape[0]),
            },
        }
