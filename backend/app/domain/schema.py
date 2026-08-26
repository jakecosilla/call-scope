from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class EmotionalTone(str, Enum):
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    FRUSTRATED = "frustrated"
    UPSET = "upset"
    DISTRESSED = "distressed"


class EmotionalIntensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BackgroundNoiseSeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AudioQuality(str, Enum):
    CLEAR = "clear"
    SLIGHTLY_IMPAIRED = "slightly_impaired"
    SEVERELY_IMPAIRED = "severely_impaired"


class PredictionResult(BaseModel):
    emotional_tone: EmotionalTone
    emotional_intensity: EmotionalIntensity
    background_noise_present: bool
    background_noise_type: str = ""
    background_noise_severity: BackgroundNoiseSeverity
    audio_quality: AudioQuality
    speaker_overlap_present: bool
    long_silence_present: bool
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("background_noise_type")
    @classmethod
    def validate_noise_type(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_noise_invariants(self) -> "PredictionResult":
        if not self.background_noise_present:
            self.background_noise_type = ""
            self.background_noise_severity = BackgroundNoiseSeverity.NONE
        return self


class InternalInferenceMetadata(BaseModel):
    pipeline_version: str
    approach: str
    preprocessing_duration_seconds: float
    inference_duration_seconds: float
    total_duration_seconds: float
    real_time_factor: float
    audio_duration_seconds: float
    estimated_cost_usd: float
    estimated_cost_per_audio_minute_usd: float
    raw_acoustic_features: dict | None = None


class CallAnalysisFileResult(BaseModel):
    file_id: str
    filename: str
    status: str
    error_message: str | None = None
    prediction: PredictionResult | None = None
    metadata: InternalInferenceMetadata | None = None


class BatchSummary(BaseModel):
    batch_id: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    progress_percentage: float
    created_at: str
    completed_at: str | None = None
    files: list[CallAnalysisFileResult] = []


class ManifestRow(BaseModel):
    name: str
    result_json: str | None = None
