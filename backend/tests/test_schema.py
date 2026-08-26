import pytest
from pydantic import ValidationError

from app.domain.schema import (
    AudioQuality,
    BackgroundNoiseSeverity,
    EmotionalIntensity,
    EmotionalTone,
    PredictionResult,
)


def test_prediction_result_schema_valid():
    data = {
        "emotional_tone": "upset",
        "emotional_intensity": "high",
        "background_noise_present": False,
        "background_noise_type": "",
        "background_noise_severity": "none",
        "audio_quality": "clear",
        "speaker_overlap_present": False,
        "long_silence_present": False,
        "confidence": 0.82,
    }
    result = PredictionResult.model_validate(data)
    assert result.emotional_tone == EmotionalTone.UPSET
    assert result.emotional_intensity == EmotionalIntensity.HIGH
    assert result.background_noise_present is False
    assert result.background_noise_type == ""
    assert result.background_noise_severity == BackgroundNoiseSeverity.NONE
    assert result.audio_quality == AudioQuality.CLEAR
    assert result.speaker_overlap_present is False
    assert result.long_silence_present is False
    assert result.confidence == 0.82


def test_prediction_result_invalid_enum():
    data = {
        "emotional_tone": "invalid_tone",
        "emotional_intensity": "low",
        "background_noise_present": False,
        "background_noise_type": "",
        "background_noise_severity": "low",
        "audio_quality": "clear",
        "speaker_overlap_present": False,
        "long_silence_present": False,
        "confidence": 0.8,
    }
    with pytest.raises(ValidationError):
        PredictionResult.model_validate(data)


def test_prediction_result_confidence_out_of_bounds():
    data = {
        "emotional_tone": "neutral",
        "emotional_intensity": "low",
        "background_noise_present": False,
        "background_noise_type": "",
        "background_noise_severity": "none",
        "audio_quality": "clear",
        "speaker_overlap_present": False,
        "long_silence_present": False,
        "confidence": 1.5,
    }
    with pytest.raises(ValidationError):
        PredictionResult.model_validate(data)
