"""Face mesh rendering helpers."""

from __future__ import annotations

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image

from config import (
    MESH_LINE_COLOR,
    MESH_LINE_THICKNESS,
    MESH_POINT_COLOR,
    MESH_POINT_RADIUS,
    OUTPUT_DIR,
)


def render_highlighted_mesh(image_bgr: np.ndarray, face_landmarks, base_name: str) -> str:
    """Draw the MediaPipe face mesh on the image and save a highlighted JPEG."""

    highlighted = image_bgr.copy()
    if hasattr(mp, "solutions"):
        drawing_utils = mp.solutions.drawing_utils
        connections = mp.solutions.face_mesh.FACEMESH_TESSELATION
        landmark_payload = face_landmarks
    else:
        from mediapipe.tasks.python import vision

        drawing_utils = vision.drawing_utils
        connections = vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION
        landmark_payload = face_landmarks

    drawing_utils.draw_landmarks(
        image=highlighted,
        landmark_list=landmark_payload,
        connections=connections,
        landmark_drawing_spec=drawing_utils.DrawingSpec(
            color=MESH_POINT_COLOR,
            thickness=MESH_LINE_THICKNESS,
            circle_radius=MESH_POINT_RADIUS,
        ),
        connection_drawing_spec=drawing_utils.DrawingSpec(
            color=MESH_LINE_COLOR,
            thickness=MESH_LINE_THICKNESS,
            circle_radius=1,
        ),
    )

    output_filename = f"{base_name}_highlighted.jpg"
    output_path = OUTPUT_DIR / output_filename
    image_rgb = cv2.cvtColor(highlighted, cv2.COLOR_BGR2RGB)
    Image.fromarray(image_rgb).save(output_path, format="JPEG", quality=95)
    return output_filename
