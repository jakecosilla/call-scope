import time

from app.audio.processor import AudioFeatures, AudioProcessor
from app.domain.schema import (
    AudioQuality,
    EmotionalIntensity,
    EmotionalTone,
    PredictionResult,
)


class AcousticPipelineInference:
    APPROACH_NAME = "Acoustic Signal Engine"

    @classmethod
    def predict(
        cls, audio_bytes: bytes, filename: str
    ) -> tuple[PredictionResult, AudioFeatures, float, float]:
        t0 = time.perf_counter()
        y, sr = AudioProcessor.load_audio(audio_bytes, filename)
        features = AudioProcessor.extract_features(y, sr)
        t1 = time.perf_counter()

        tone, intensity, margin_score = cls._predict_emotion(features)
        t2 = time.perf_counter()

        # Dynamic confidence scoring based on acoustic feature margin, SNR, and quality penalty
        quality_penalty = (
            0.0
            if features.audio_quality == AudioQuality.CLEAR
            else (0.15 if features.audio_quality == AudioQuality.SLIGHTLY_IMPAIRED else 0.35)
        )
        snr_factor = max(0.0, min(1.0, features.snr_db / 30.0))

        raw_confidence = (margin_score * 0.6) + (snr_factor * 0.4) - quality_penalty
        confidence = float(max(0.35, min(0.98, round(raw_confidence, 2))))

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
        preproc_duration = t1 - t0
        inference_duration = t2 - t1
        return result, features, preproc_duration, inference_duration

    @classmethod
    def _predict_emotion(
        cls, f: AudioFeatures
    ) -> tuple[EmotionalTone, EmotionalIntensity, float]:
        # Generalizable statistical pitch variability & energy dynamics
        pitch_variability = f.pitch_std
        energy_spikes = f.rms_max / (f.rms_mean + 1e-5)

        if pitch_variability > 75.0 and f.rms_max > 0.35 and energy_spikes > 6.0:
            return EmotionalTone.DISTRESSED, EmotionalIntensity.HIGH, 0.88

        if pitch_variability > 50.0 and f.rms_max > 0.30:
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH, 0.84

        if pitch_variability > 35.0 and f.rms_std > 0.04:
            return EmotionalTone.FRUSTRATED, EmotionalIntensity.MEDIUM, 0.76

        if pitch_variability < 20.0 and f.rms_std < 0.02 and f.speech_ratio > 0.40:
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM, 0.79

        return EmotionalTone.NEUTRAL, EmotionalIntensity.LOW, 0.82
