"""Assembly helpers for the final analysis response."""

from __future__ import annotations

from datetime import datetime

from image_tokens import build_signed_image_url
from measurements import MeasurementResult
from schemas import (
    AnalysisResponse,
    BeardAnalysis,
    BeardRatings,
    EyeAnalysis,
    EyeRatings,
    EyebrowAnalysis,
    EyebrowRatings,
    FaceFeatures,
    FaceShapeAnalysis,
    FaceShapeCharacteristics,
    FeatureScores,
    ImageQuality,
    ImageReferences,
    LipAnalysis,
    LipRatings,
    MeasurementSet,
    NoseAnalysis,
    NoseRatings,
    ScoringSummary,
    ShapeProbabilities,
    SymmetryResult,
)


def build_analysis_response(
    quality: dict[str, float | str | None],
    measurements: MeasurementResult,
    eyes: dict[str, float | str],
    eyebrows: dict[str, float | str],
    nose: dict[str, float | str],
    lips: dict[str, float | str],
    beard: dict[str, float | str | bool | dict[str, float]],
    face_shape: dict[str, float | str | dict | list[str]],
    symmetry: dict[str, float],
    scoring: dict[str, dict | float | str],
    original_filename: str,
    highlighted_filename: str,
    expires_at: datetime,
) -> AnalysisResponse:
    """Build the full typed analysis response from computed analysis blocks."""

    ratings = scoring["ratings"]
    return AnalysisResponse(
        message="Face analysis completed successfully.",
        image_quality=ImageQuality(**quality),
        measurements=MeasurementSet(**measurements.to_response_dict()),
        features=FaceFeatures(
            eyes=EyeAnalysis(
                size=str(eyes["size"]),
                shape=str(eyes["shape"]),
                spacing=str(eyes["spacing"]),
                symmetry=str(eyes["symmetry"]),
                mean_width=float(eyes["mean_width"]),
                aspect_ratio=float(eyes["aspect_ratio"]),
                spacing_ratio=float(eyes["spacing_ratio"]),
                symmetry_difference_pct=float(eyes["symmetry_difference_pct"]),
                ratings=EyeRatings(**ratings["eyes"]),
            ),
            eyebrows=EyebrowAnalysis(
                thickness=str(eyebrows["thickness"]),
                arch=str(eyebrows["arch"]),
                spacing=str(eyebrows["spacing"]),
                symmetry=str(eyebrows["symmetry"]),
                average_height=float(eyebrows["average_height"]),
                spacing_ratio=float(eyebrows["spacing_ratio"]),
                arch_delta=float(eyebrows["arch_delta"]),
                symmetry_difference_pct=float(eyebrows["symmetry_difference_pct"]),
                ratings=EyebrowRatings(**ratings["eyebrows"]),
            ),
            nose=NoseAnalysis(
                width=str(nose["width"]),
                length=str(nose["length"]),
                bridge=str(nose["bridge"]),
                shape=str(nose["shape"]),
                proportion=str(nose["proportion"]),
                width_ratio=float(nose["width_ratio"]),
                length_ratio=float(nose["length_ratio"]),
                bridge_ratio=float(nose["bridge_ratio"]),
                ratings=NoseRatings(**ratings["nose"]),
            ),
            lips=LipAnalysis(
                width=str(lips["width"]),
                thickness=str(lips["thickness"]),
                shape=str(lips["shape"]),
                cupid_bow=str(lips["cupid_bow"]),
                symmetry=str(lips["symmetry"]),
                proportion=str(lips["proportion"]),
                width_ratio=float(lips["width_ratio"]),
                total_thickness=float(lips["total_thickness"]),
                upper_lower_ratio=float(lips["upper_lower_ratio"]),
                cupid_bow_offset=float(lips["cupid_bow_offset"]),
                symmetry_difference=float(lips["symmetry_difference"]),
                ratings=LipRatings(**ratings["lips"]),
            ),
            beard=BeardAnalysis(
                detected=bool(beard["detected"]),
                style=str(beard["style"]),
                density=str(beard["density"]),
                coverage=str(beard["coverage"]),
                avg_intensity=float(beard["avg_intensity"]),
                edge_density=float(beard["edge_density"]),
                texture_variation=float(beard["texture_variation"]),
                mustache_score=float(beard["mustache_score"]),
                ratings=BeardRatings(**beard["ratings"]),
            ),
            face_shape=FaceShapeAnalysis(
                primary_shape=str(face_shape["primary_shape"]),
                width_to_length_ratio=float(face_shape["width_to_length_ratio"]),
                jaw_ratio=float(face_shape["jaw_ratio"]),
                forehead_ratio=float(face_shape["forehead_ratio"]),
                shape_probabilities=ShapeProbabilities(**face_shape["shape_probabilities"]),
                primary_percentage=float(face_shape["primary_percentage"]),
                recommendations=list(face_shape["recommendations"]),
                characteristics=FaceShapeCharacteristics(**face_shape["characteristics"]),
                harmony_score=float(ratings["face_shape"]["overall"]),
            ),
        ),
        symmetry=SymmetryResult(**symmetry),
        scoring=ScoringSummary(
            feature_scores=FeatureScores(**scoring["feature_scores"]),
            golden_ratio_score=float(scoring["golden_ratio_score"]),
            overall_rating=float(scoring["overall_rating"]),
            percentage=float(scoring["percentage"]),
            rating_message=str(scoring["rating_message"]),
        ),
        images=ImageReferences(
            original_filename=original_filename,
            highlighted_filename=highlighted_filename,
            original_url=build_signed_image_url(original_filename, expires_at),
            highlighted_url=build_signed_image_url(highlighted_filename, expires_at),
        ),
        expires_at=expires_at,
        privacy_note="Images are automatically deleted after 30 minutes.",
    )
