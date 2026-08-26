from app.audio.processor import AudioFeatures, AudioProcessor
from app.domain.schema import (
    AudioQuality,
    EmotionalIntensity,
    EmotionalTone,
    PredictionResult,
)


class AcousticPipelineInference:
    APPROACH_NAME = "Approach A - Acoustic Signal & Rule Engine"

    @classmethod
    def predict(cls, audio_bytes: bytes, filename: str) -> tuple[PredictionResult, AudioFeatures]:
        y, sr = AudioProcessor.load_audio(audio_bytes, filename)
        features = AudioProcessor.extract_features(y, sr)

        tone, intensity, tone_confidence = cls._predict_emotion(features, filename)

        base_confidence = (tone_confidence + (1.0 if features.audio_quality == AudioQuality.CLEAR else 0.8)) / 2.0
        confidence = float(max(0.40, min(0.95, round(base_confidence, 2))))

        result = PredictionResult(
            emotional_tone=tone,
            emotional_intensity=intensity,
            background_noise_present=features.background_noise_present,
            background_noise_type=features.background_noise_type,
            background_noise_severity=features.background_noise_severity,
            audio_quality=features.audio_quality,
            speaker_overlap_present=features.speaker_overlap_present,
            long_silence_present=features.long_silence_present,
            confidence=confidence,
        )
        return result, features

    @classmethod
    def _predict_emotion(
        cls, f: AudioFeatures, filename: str
    ) -> tuple[EmotionalTone, EmotionalIntensity, float]:
        if f.pitch_std > 50.0 and f.rms_max > 0.40 and f.duration_seconds < 40.0:
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH, 0.82

        if f.duration_seconds > 100.0 and f.speech_ratio > 0.45:
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM, 0.82

        if f.pitch_std > 150.0 and f.rms_mean < 0.03:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.MEDIUM, 0.82

        if f.pitch_std > 55.0 and f.rms_max > 0.35 and f.snr_db < 10.0:
            return EmotionalTone.DISTRESSED, EmotionalIntensity.HIGH, 0.80

        if f.pitch_std > 45.0 and f.rms_std > 0.03:
            return EmotionalTone.FRUSTRATED, EmotionalIntensity.MEDIUM, 0.78

        return EmotionalTone.NEUTRAL, EmotionalIntensity.MEDIUM, 0.82
