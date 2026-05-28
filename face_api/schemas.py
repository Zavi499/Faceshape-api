"""Pydantic models for API responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class APIErrorResponse(BaseModel):
    """Standard error payload returned by the API."""

    success: bool = False
    message: str
    detail: str


class ImageQuality(BaseModel):
    """Computed quality indicators for the uploaded image."""

    lighting: str
    face_angle: str
    blur_score: float
    quality_score: float
    recommendation: str | None = None


class MeasurementSet(BaseModel):
    """Top-level geometric measurements derived from facial landmarks."""

    face_width: float
    face_height: float
    eye_span: float
    interocular_distance: float
    forehead_width: float
    jaw_width: float
    mouth_width: float
    nose_length: float
    nose_width: float


class EyeRatings(BaseModel):
    """Numeric ratings for eye analysis categories."""

    shape: float
    size: float
    spacing: float
    symmetry: float
    overall: float


class EyeAnalysis(BaseModel):
    """Descriptive and numeric analysis of the eyes."""

    size: str
    shape: str
    spacing: str
    symmetry: str
    mean_width: float
    aspect_ratio: float
    spacing_ratio: float
    symmetry_difference_pct: float
    ratings: EyeRatings


class EyebrowRatings(BaseModel):
    """Numeric ratings for eyebrow analysis categories."""

    arch: float
    spacing: float
    thickness: float
    overall: float


class EyebrowAnalysis(BaseModel):
    """Descriptive and numeric analysis of the eyebrows."""

    thickness: str
    arch: str
    spacing: str
    symmetry: str
    average_height: float
    spacing_ratio: float
    arch_delta: float
    symmetry_difference_pct: float
    ratings: EyebrowRatings


class NoseRatings(BaseModel):
    """Numeric ratings for nose analysis categories."""

    width: float
    length: float
    bridge: float
    proportion: float
    overall: float


class NoseAnalysis(BaseModel):
    """Descriptive and numeric analysis of the nose."""

    width: str
    length: str
    bridge: str
    shape: str
    proportion: str
    width_ratio: float
    length_ratio: float
    bridge_ratio: float
    ratings: NoseRatings


class LipRatings(BaseModel):
    """Numeric ratings for lip analysis categories."""

    shape: float
    thickness: float
    width: float
    cupid_bow: float
    proportion: float
    overall: float


class LipAnalysis(BaseModel):
    """Descriptive and numeric analysis of the lips."""

    width: str
    thickness: str
    shape: str
    cupid_bow: str
    symmetry: str
    proportion: str
    width_ratio: float
    total_thickness: float
    upper_lower_ratio: float
    cupid_bow_offset: float
    symmetry_difference: float
    ratings: LipRatings


class BeardRatings(BaseModel):
    """Numeric ratings for beard analysis categories."""

    density: float
    style: float
    overall: float


class BeardAnalysis(BaseModel):
    """Detected beard characteristics and supporting metrics."""

    detected: bool
    style: str
    density: str
    coverage: str
    avg_intensity: float
    edge_density: float
    texture_variation: float
    mustache_score: float
    ratings: BeardRatings


class ShapeProbabilities(BaseModel):
    """Probability distribution across supported face shapes."""

    round: float = Field(alias="Round")
    oval: float = Field(alias="Oval")
    oblong: float = Field(alias="Oblong")
    square: float = Field(alias="Square")
    heart: float = Field(alias="Heart")
    diamond: float = Field(alias="Diamond")

    model_config = {"populate_by_name": True}


class FaceShapeCharacteristics(BaseModel):
    """Qualitative descriptors for a face shape profile."""

    apple_cheeks: str
    cheekbone: str
    chin: str
    temple: str


class FaceShapeAnalysis(BaseModel):
    """Analysis result for overall face shape."""

    primary_shape: str
    width_to_length_ratio: float
    jaw_ratio: float
    forehead_ratio: float
    shape_probabilities: ShapeProbabilities
    primary_percentage: float
    recommendations: list[str]
    characteristics: FaceShapeCharacteristics
    harmony_score: float


class FaceFeatures(BaseModel):
    """Container for all feature-specific analyses."""

    eyes: EyeAnalysis
    eyebrows: EyebrowAnalysis
    nose: NoseAnalysis
    lips: LipAnalysis
    beard: BeardAnalysis
    face_shape: FaceShapeAnalysis


class SymmetryResult(BaseModel):
    """Symmetry score and component pair scores."""

    eye_width_score: float
    brow_length_score: float
    jaw_balance_score: float
    symmetry_score: float


class FeatureScores(BaseModel):
    """Weighted feature scores used for the overall attractiveness rating."""

    eyes: float
    nose: float
    lips: float
    eyebrows: float
    face_shape: float


class ScoringSummary(BaseModel):
    """Overall scoring summary for the analyzed face."""

    feature_scores: FeatureScores
    golden_ratio_score: float
    overall_rating: float
    percentage: float
    rating_message: str


class ImageReferences(BaseModel):
    """Stored image filenames and API URLs."""

    original_filename: str
    highlighted_filename: str
    original_url: str
    highlighted_url: str


class AnalysisResponse(BaseModel):
    """Successful face analysis response."""

    success: bool = True
    message: str
    image_quality: ImageQuality
    measurements: MeasurementSet
    features: FaceFeatures
    symmetry: SymmetryResult
    scoring: ScoringSummary
    images: ImageReferences
    expires_at: datetime
    privacy_note: str


class DeleteImageResponse(BaseModel):
    """Response returned after manual image deletion."""

    deleted: bool
    filename: str


class DetailedMetric(BaseModel):
    """A detailed measurement with interpretation for focused analysis endpoints."""

    name: str
    measured: float
    unit: str
    ideal: float | None = None
    score: float | None = None
    assessment: str
    detail: str


class PairedFeatureComparison(BaseModel):
    """Left-right comparison block used by symmetry analysis endpoints."""

    feature: str
    left_value: float
    right_value: float
    unit: str
    difference_pct: float
    score: float
    detail: str


class AlignmentMetric(BaseModel):
    """Alignment measurement used by symmetry analysis endpoints."""

    name: str
    value: float
    unit: str
    score: float
    assessment: str
    detail: str


class SymmetryAnalysisResponse(BaseModel):
    """Detailed response for the face symmetry endpoint."""

    success: bool = True
    message: str
    image_quality: ImageQuality
    overall_score: float
    verdict: str
    paired_features: list[PairedFeatureComparison]
    alignment_metrics: list[AlignmentMetric]
    summary: str


class EyeShapeAnalysisResponse(BaseModel):
    """Detailed response for the eye shape endpoint."""

    success: bool = True
    message: str
    image_quality: ImageQuality
    primary_shape: str
    size_classification: str
    spacing_classification: str
    symmetry_classification: str
    overall_score: float
    metrics: list[DetailedMetric]
    observations: list[str]
    summary: str


class LipShapeAnalysisResponse(BaseModel):
    """Detailed response for the lip shape endpoint."""

    success: bool = True
    message: str
    image_quality: ImageQuality
    primary_shape: str
    width_classification: str
    thickness_classification: str
    symmetry_classification: str
    overall_score: float
    metrics: list[DetailedMetric]
    observations: list[str]
    summary: str


class NoseShapeAnalysisResponse(BaseModel):
    """Detailed response for the nose shape endpoint."""

    success: bool = True
    message: str
    image_quality: ImageQuality
    primary_shape: str
    width_classification: str
    length_classification: str
    bridge_classification: str
    overall_score: float
    metrics: list[DetailedMetric]
    observations: list[str]
    summary: str


class GoldenRatioComponent(BaseModel):
    """Individual component of the golden-ratio analysis."""

    name: str
    measured: float
    ideal: float
    score: float
    weight: float
    detail: str


class GoldenRatioAnalysisResponse(BaseModel):
    """Detailed response for the golden-ratio endpoint."""

    success: bool = True
    message: str
    image_quality: ImageQuality
    overall_score: float
    components: list[GoldenRatioComponent]
    strongest_components: list[str]
    improvement_areas: list[str]
    summary: str


class AgePrediction(BaseModel):
    """Confidence entry for age prediction buckets."""

    range: str
    confidence: float


class FaceAgeAnalysisResponse(BaseModel):
    """Detailed response for the face age endpoint."""

    success: bool = True
    message: str
    image_quality: ImageQuality
    model_name: str
    predicted_age_range: str
    estimated_age: float
    confidence: float
    reliability: str
    top_predictions: list[AgePrediction]
    analysis_notes: list[str]
    summary: str
