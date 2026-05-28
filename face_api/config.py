"""Application configuration and facial landmark constants."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
MODELS_DIR = BASE_DIR / "models"
IMAGE_TTL_MINUTES = 30
MAX_FILE_SIZE_MB = 10
MIN_RESOLUTION = (200, 200)
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "https://facesanalyzer.com,https://www.facesanalyzer.com",
    ).split(",")
    if origin.strip()
]
GOLDEN_RATIO = 1.618
FACE_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
FACE_LANDMARKER_MODEL_PATH = MODELS_DIR / "face_landmarker.task"
AGE_MODEL_PROTO_URL = "https://raw.githubusercontent.com/spmallick/learnopencv/master/AgeGender/age_deploy.prototxt"
AGE_MODEL_WEIGHTS_URL = "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/models/age_net.caffemodel"
AGE_MODEL_PROTO_PATH = MODELS_DIR / "age_deploy.prototxt"
AGE_MODEL_WEIGHTS_PATH = MODELS_DIR / "age_net.caffemodel"
AGE_MODEL_INPUT_SIZE = (227, 227)
AGE_MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
AGE_BUCKETS = [
    "(0-2)",
    "(4-6)",
    "(8-12)",
    "(15-20)",
    "(25-32)",
    "(38-43)",
    "(48-53)",
    "(60-100)",
]
AGE_BUCKET_CENTERS = [1.0, 5.0, 10.0, 17.5, 28.5, 40.5, 50.5, 80.0]
IDEAL_PROPORTIONS = {
    "eye_spacing_ratio": 0.46,
    "nose_length_ratio": 0.33,
    "mouth_width_ratio": 0.50,
    "face_ratio": 1.00,
}
FEATURE_WEIGHTS = {
    "eyes": 0.30,
    "nose": 0.25,
    "lips": 0.20,
    "eyebrows": 0.15,
    "face_shape": 0.10,
}
CLEANUP_INTERVAL_MINUTES = 5
META_SUFFIX = ".meta.json"
MESH_LINE_COLOR = (0, 255, 0)
MESH_POINT_COLOR = (0, 128, 255)
MESH_LINE_THICKNESS = 1
MESH_POINT_RADIUS = 1

EYES_LEFT = [33, 160, 158, 133, 153, 144]
EYES_RIGHT = [362, 385, 387, 263, 373, 380]
BROW_LEFT = [70, 63, 105, 66, 107]
BROW_RIGHT = [336, 296, 334, 293, 300]
NOSE_TIP = 4
NOSE_BRIDGE = 168
NOSE_L = 129
NOSE_R = 358
LIPS_TOP = 13
LIPS_BOT = 14
LIPS_L = 61
LIPS_R = 291
JAW = [10, 234, 152, 454, 323, 93]
FOREHEAD = [10, 67, 109, 338, 297]


def ensure_output_dir() -> Path:
    """Ensure the configured output directory exists and return it."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def ensure_models_dir() -> Path:
    """Ensure the configured model directory exists and return it."""

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def generate_image_filenames(now: datetime | None = None) -> dict[str, str]:
    """Generate unique original and highlighted image filenames."""

    current_time = now or datetime.now()
    base = f"api_{current_time:%Y%m%d_%H%M%S}_{uuid4().hex[:8]}"
    return {
        "base": base,
        "original": f"{base}.jpg",
        "highlighted": f"{base}_highlighted.jpg",
    }
