"""FastAPI application entrypoint for single-face analysis."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from mimetypes import guess_type

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

from age_estimator import AgeEstimator
from cleanup import delete_image_file, get_expires_at, get_image_path, start_cleanup_scheduler, stop_cleanup_scheduler, write_image_metadata
from config import OUTPUT_DIR, ensure_output_dir, generate_image_filenames
from detailed_analysis import (
    build_eye_shape_report,
    build_golden_ratio_report,
    build_lip_shape_report,
    build_nose_shape_report,
    build_symmetry_report,
)
from detector import FaceMeshDetector
from features import analyze_beard, analyze_eyebrows, analyze_eyes, analyze_face_shape, analyze_lips, analyze_nose
from measurements import compute_measurements, to_pixel_landmarks
from renderer import render_highlighted_mesh
from response_builder import build_analysis_response
from schemas import (
    AgePrediction,
    AnalysisResponse,
    APIErrorResponse,
    DeleteImageResponse,
    EyeShapeAnalysisResponse,
    FaceAgeAnalysisResponse,
    GoldenRatioAnalysisResponse,
    ImageQuality,
    LipShapeAnalysisResponse,
    NoseShapeAnalysisResponse,
    SymmetryAnalysisResponse,
)
from scorer import calculate_scores
from security import OriginGuardMiddleware
from symmetry import compute_symmetry
from validator import FileValidationError, ValidatedImage, analyze_image_quality, validate_upload_file

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass(slots=True)
class PreparedFaceAnalysis:
    """Shared validated image and landmark context for face-analysis endpoints."""

    validated_image: ValidatedImage
    face_landmarks: object
    pixel_landmarks: dict[int, tuple[float, float]]
    measurements: object
    image_quality: dict[str, float | str | None]


class APIError(Exception):
    """Structured application exception translated into the standard error payload."""

    def __init__(self, status_code: int, message: str, detail: str) -> None:
        """Store the HTTP status code and payload fields for the error response."""

        super().__init__(detail)
        self.status_code = status_code
        self.message = message
        self.detail = detail


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and tear down shared services for the application."""

    ensure_output_dir()
    app.state.detector = FaceMeshDetector()
    app.state.age_estimator = None
    start_cleanup_scheduler()
    try:
        yield
    finally:
        app.state.detector.close()
        stop_cleanup_scheduler()


app = FastAPI(
    title="Face Analysis API",
    version="1.1.0",
    description="Single-face analysis API powered by FastAPI, MediaPipe, and dedicated endpoint-specific facial analysis flows.",
    lifespan=lifespan,
)
app.add_middleware(OriginGuardMiddleware)


def save_original_image(image: Image.Image, filename: str) -> None:
    """Save the original upload as a JPEG file in the output directory."""

    output_path = OUTPUT_DIR / filename
    image.convert("RGB").save(output_path, format="JPEG", quality=95)


def get_age_estimator(request: Request) -> AgeEstimator:
    """Return a lazily initialized age estimator stored on the app state."""

    estimator = getattr(request.app.state, "age_estimator", None)
    if estimator is None:
        estimator = AgeEstimator()
        request.app.state.age_estimator = estimator
    return estimator


async def prepare_single_face_analysis(request: Request, file: UploadFile) -> PreparedFaceAnalysis:
    """Validate an upload, enforce the single-face rule, and compute shared analysis inputs."""

    content = await file.read()
    try:
        validated_image = validate_upload_file(file, content)
    except FileValidationError as exc:
        raise APIError(400, exc.message, exc.detail) from exc

    detector: FaceMeshDetector = request.app.state.detector
    detected_faces = detector.detect(validated_image.bgr_image)
    if len(detected_faces) == 0:
        raise APIError(
            422,
            "No face detected in the image.",
            "MediaPipe could not locate a face in the uploaded image.",
        )
    if len(detected_faces) > 1:
        raise APIError(
            422,
            "Multiple faces detected. Please upload an image with exactly one face.",
            "Single-face analysis only supports images containing exactly one face.",
        )

    face_landmarks = detected_faces[0]
    pixel_landmarks = to_pixel_landmarks(face_landmarks, validated_image.width, validated_image.height)
    image_quality = analyze_image_quality(validated_image.bgr_image, pixel_landmarks)
    measurements = compute_measurements(pixel_landmarks)
    return PreparedFaceAnalysis(
        validated_image=validated_image,
        face_landmarks=face_landmarks,
        pixel_landmarks=pixel_landmarks,
        measurements=measurements,
        image_quality=image_quality,
    )


@app.exception_handler(APIError)
async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
    """Return standardized JSON for known application errors."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return standardized JSON for malformed requests."""

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "Invalid request.",
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Return a safe 500 response while logging the underlying traceback."""

    logger.exception("Unexpected server error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Unexpected server error.",
            "detail": "An unexpected error occurred while processing the request.",
        },
    )


@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": APIErrorResponse},
        422: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def analyze_face(request: Request, file: UploadFile = File(...)) -> AnalysisResponse:
    """Analyze a single uploaded face image and return a detailed JSON response."""

    prepared = await prepare_single_face_analysis(request, file)

    now = datetime.now(timezone.utc)
    expires_at = get_expires_at(now)
    filenames = generate_image_filenames()
    original_filename = filenames["original"]
    highlighted_filename = filenames["highlighted"]
    highlighted_created = False
    original_created = False

    try:
        save_original_image(prepared.validated_image.pil_image, original_filename)
        original_created = True
        write_image_metadata(original_filename, now, expires_at)

        eyes = analyze_eyes(prepared.measurements)
        eyebrows = analyze_eyebrows(prepared.measurements, prepared.pixel_landmarks)
        nose = analyze_nose(prepared.measurements)
        lips = analyze_lips(prepared.measurements)
        beard = analyze_beard(prepared.validated_image.bgr_image, prepared.pixel_landmarks)
        face_shape = analyze_face_shape(prepared.measurements)
        symmetry = compute_symmetry(prepared.measurements)
        scoring = calculate_scores(prepared.measurements, eyes, eyebrows, nose, lips, face_shape)

        render_highlighted_mesh(prepared.validated_image.bgr_image, prepared.face_landmarks, filenames["base"])
        highlighted_created = True
        write_image_metadata(highlighted_filename, now, expires_at)

        return build_analysis_response(
            quality=prepared.image_quality,
            measurements=prepared.measurements,
            eyes=eyes,
            eyebrows=eyebrows,
            nose=nose,
            lips=lips,
            beard=beard,
            face_shape=face_shape,
            symmetry=symmetry,
            scoring=scoring,
            original_filename=original_filename,
            highlighted_filename=highlighted_filename,
            expires_at=expires_at,
        )
    except APIError:
        if highlighted_created:
            delete_image_file(highlighted_filename)
        if original_created:
            delete_image_file(original_filename)
        raise
    except Exception:
        if highlighted_created:
            delete_image_file(highlighted_filename)
        if original_created:
            delete_image_file(original_filename)
        raise


@app.post(
    "/analyze/symmetry",
    response_model=SymmetryAnalysisResponse,
    responses={400: {"model": APIErrorResponse}, 422: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
)
async def analyze_face_symmetry(request: Request, file: UploadFile = File(...)) -> SymmetryAnalysisResponse:
    """Analyze detailed facial symmetry from a single uploaded face image."""

    prepared = await prepare_single_face_analysis(request, file)
    report = build_symmetry_report(prepared.measurements, prepared.pixel_landmarks)
    return SymmetryAnalysisResponse(
        message="Face symmetry analysis completed successfully.",
        image_quality=ImageQuality(**prepared.image_quality),
        overall_score=report["overall_score"],
        verdict=report["verdict"],
        paired_features=report["paired_features"],
        alignment_metrics=report["alignment_metrics"],
        summary=report["summary"],
    )


@app.post(
    "/analyze/lips",
    response_model=LipShapeAnalysisResponse,
    responses={400: {"model": APIErrorResponse}, 422: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
)
async def analyze_lip_shape(request: Request, file: UploadFile = File(...)) -> LipShapeAnalysisResponse:
    """Analyze detailed lip shape from a single uploaded face image."""

    prepared = await prepare_single_face_analysis(request, file)
    report = build_lip_shape_report(prepared.measurements, prepared.pixel_landmarks)
    return LipShapeAnalysisResponse(
        message="Lip shape analysis completed successfully.",
        image_quality=ImageQuality(**prepared.image_quality),
        primary_shape=report["primary_shape"],
        width_classification=report["width_classification"],
        thickness_classification=report["thickness_classification"],
        symmetry_classification=report["symmetry_classification"],
        overall_score=report["overall_score"],
        metrics=report["metrics"],
        observations=report["observations"],
        summary=report["summary"],
    )


@app.post(
    "/analyze/nose",
    response_model=NoseShapeAnalysisResponse,
    responses={400: {"model": APIErrorResponse}, 422: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
)
async def analyze_nose_shape(request: Request, file: UploadFile = File(...)) -> NoseShapeAnalysisResponse:
    """Analyze detailed nose shape from a single uploaded face image."""

    prepared = await prepare_single_face_analysis(request, file)
    report = build_nose_shape_report(prepared.measurements, prepared.pixel_landmarks)
    return NoseShapeAnalysisResponse(
        message="Nose shape analysis completed successfully.",
        image_quality=ImageQuality(**prepared.image_quality),
        primary_shape=report["primary_shape"],
        width_classification=report["width_classification"],
        length_classification=report["length_classification"],
        bridge_classification=report["bridge_classification"],
        overall_score=report["overall_score"],
        metrics=report["metrics"],
        observations=report["observations"],
        summary=report["summary"],
    )


@app.post(
    "/analyze/age",
    response_model=FaceAgeAnalysisResponse,
    responses={400: {"model": APIErrorResponse}, 422: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
)
async def analyze_face_age(request: Request, file: UploadFile = File(...)) -> FaceAgeAnalysisResponse:
    """Estimate age using a dedicated DNN age-estimation model."""

    prepared = await prepare_single_face_analysis(request, file)
    try:
        age_result = get_age_estimator(request).estimate(prepared.validated_image.bgr_image, prepared.pixel_landmarks)
    except ValueError as exc:
        raise APIError(422, "Unable to estimate age from the image.", str(exc)) from exc
    except Exception as exc:
        raise APIError(500, "Age estimation model unavailable.", str(exc)) from exc

    summary = (
        f"The dedicated age model predicts the face most strongly in the {age_result['predicted_age_range']} range "
        f"with {age_result['confidence']}% confidence, and the weighted average estimate is {age_result['estimated_age']} years."
    )
    notes = [
        "Age is estimated from a dedicated deep neural network rather than from facial ratios alone.",
        "The exact number should be treated as an approximate visual age, while the age bucket is usually the more stable result.",
        f"The model reliability for this prediction is marked as {age_result['reliability']}.",
    ]
    return FaceAgeAnalysisResponse(
        message="Face age analysis completed successfully.",
        image_quality=ImageQuality(**prepared.image_quality),
        model_name=age_result["model_name"],
        predicted_age_range=age_result["predicted_age_range"],
        estimated_age=age_result["estimated_age"],
        confidence=age_result["confidence"],
        reliability=age_result["reliability"],
        top_predictions=[AgePrediction(**item) for item in age_result["top_predictions"]],
        analysis_notes=notes,
        summary=summary,
    )


@app.post(
    "/analyze/eyes",
    response_model=EyeShapeAnalysisResponse,
    responses={400: {"model": APIErrorResponse}, 422: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
)
async def analyze_eye_shape(request: Request, file: UploadFile = File(...)) -> EyeShapeAnalysisResponse:
    """Analyze detailed eye shape from a single uploaded face image."""

    prepared = await prepare_single_face_analysis(request, file)
    report = build_eye_shape_report(prepared.measurements, prepared.pixel_landmarks)
    return EyeShapeAnalysisResponse(
        message="Eye shape analysis completed successfully.",
        image_quality=ImageQuality(**prepared.image_quality),
        primary_shape=report["primary_shape"],
        size_classification=report["size_classification"],
        spacing_classification=report["spacing_classification"],
        symmetry_classification=report["symmetry_classification"],
        overall_score=report["overall_score"],
        metrics=report["metrics"],
        observations=report["observations"],
        summary=report["summary"],
    )


@app.post(
    "/analyze/golden-ratio",
    response_model=GoldenRatioAnalysisResponse,
    responses={400: {"model": APIErrorResponse}, 422: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
)
async def analyze_golden_ratio(request: Request, file: UploadFile = File(...)) -> GoldenRatioAnalysisResponse:
    """Analyze facial harmony using a detailed golden-ratio style breakdown."""

    prepared = await prepare_single_face_analysis(request, file)
    report = build_golden_ratio_report(prepared.measurements)
    return GoldenRatioAnalysisResponse(
        message="Golden ratio analysis completed successfully.",
        image_quality=ImageQuality(**prepared.image_quality),
        overall_score=report["overall_score"],
        components=report["components"],
        strongest_components=report["strongest_components"],
        improvement_areas=report["improvement_areas"],
        summary=report["summary"],
    )


@app.get(
    "/image/{filename}",
    responses={
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def get_image(filename: str) -> StreamingResponse:
    """Stream a stored original or highlighted image from the output directory."""

    try:
        image_path = get_image_path(filename)
    except ValueError as exc:
        raise APIError(404, "Image file not found or already deleted.", str(exc)) from exc

    if not image_path.exists() or not image_path.is_file():
        raise APIError(
            404,
            "Image file not found or already deleted.",
            "The requested file does not exist or has already expired.",
        )

    media_type = guess_type(image_path.name)[0] or "application/octet-stream"
    return StreamingResponse(image_path.open("rb"), media_type=media_type)


@app.delete(
    "/image/{filename}",
    response_model=DeleteImageResponse,
    responses={
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
async def delete_image(filename: str) -> DeleteImageResponse:
    """Delete a stored original or highlighted image and its metadata."""

    try:
        deleted = delete_image_file(filename)
    except ValueError as exc:
        raise APIError(404, "Image file not found or already deleted.", str(exc)) from exc

    if not deleted:
        raise APIError(
            404,
            "Image file not found or already deleted.",
            "The requested file does not exist or has already expired.",
        )
    return DeleteImageResponse(deleted=True, filename=filename)
