"""MediaPipe face mesh detection wrapper."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

import cv2
import mediapipe as mp
import numpy as np

from config import FACE_LANDMARKER_MODEL_PATH, FACE_LANDMARKER_MODEL_URL, ensure_models_dir


class FaceMeshDetector:
    """Thin wrapper around MediaPipe Face Mesh for still-image analysis."""

    def __init__(
        self,
        max_num_faces: int = 5,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        """Initialize a reusable MediaPipe Face Mesh detector."""

        self._backend = "solutions" if hasattr(mp, "solutions") else "tasks"
        self._close_fn = lambda: None
        self._landmarker = None
        self._max_num_faces = max_num_faces

        if self._backend == "solutions":
            self._landmarker = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=max_num_faces,
                refine_landmarks=True,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self._close_fn = self._landmarker.close
            return

        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        model_path = self._ensure_face_landmarker_model()
        options = vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=max_num_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self._close_fn = self._landmarker.close

    @staticmethod
    def _ensure_face_landmarker_model() -> Path:
        """Ensure the MediaPipe face landmarker task model is available locally."""

        ensure_models_dir()
        if FACE_LANDMARKER_MODEL_PATH.exists():
            return FACE_LANDMARKER_MODEL_PATH

        with urlopen(FACE_LANDMARKER_MODEL_URL, timeout=60) as response:
            FACE_LANDMARKER_MODEL_PATH.write_bytes(response.read())
        return FACE_LANDMARKER_MODEL_PATH

    def detect(self, image_bgr: np.ndarray) -> list:
        """Detect face mesh landmarks in a BGR image."""

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        if self._backend == "solutions":
            result = self._landmarker.process(image_rgb)
            return list(result.multi_face_landmarks or [])

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        result = self._landmarker.detect(mp_image)
        return list(result.face_landmarks or [])

    def close(self) -> None:
        """Release MediaPipe resources held by the detector."""

        self._close_fn()
