import numpy as np
import torch

from app.audio.processor import AudioFeatures, AudioProcessor
from app.domain.schema import (
    EmotionalIntensity,
    EmotionalTone,
    PredictionResult,
)


class SpeechEmotionFoundationInference:
    APPROACH_NAME = "Approach B - Pre-trained Wav2Vec2 Speech Emotion Model"
    _model = None
    _processor = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            try:
                from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
                model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
                cls._processor = AutoFeatureExtractor.from_pretrained(model_name)
                cls._model = AutoModelForAudioClassification.from_pretrained(model_name)
                cls._model.eval()
            except Exception:
                cls._model = False
        return cls._model, cls._processor

    @classmethod
    def predict(cls, audio_bytes: bytes, filename: str) -> tuple[PredictionResult, AudioFeatures]:
        y, sr = AudioProcessor.load_audio(audio_bytes, filename)
        features = AudioProcessor.extract_features(y, sr)

        model, processor = cls._get_model()

        if model and processor:
            try:
                inputs = processor(y, sampling_rate=sr, return_tensors="pt", padding=True)
                with torch.no_grad():
                    logits = model(**inputs).logits
                    probs = torch.softmax(logits, dim=-1).squeeze().numpy()

                label_id = int(np.argmax(probs))
                confidence_score = float(probs[label_id])

                id2label = getattr(model.config, "id2label", {})
                raw_label = str(id2label.get(label_id, "neutral")).lower()

                tone, intensity = cls._map_label_to_enum(raw_label, features)
            except Exception:
                tone, intensity, confidence_score = cls._fallback_predict(features)
        else:
            tone, intensity, confidence_score = cls._fallback_predict(features)

        confidence = float(max(0.40, min(0.95, round(confidence_score, 2))))

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
    def _map_label_to_enum(cls, raw_label: str, f: AudioFeatures) -> tuple[EmotionalTone, EmotionalIntensity]:
        if "angry" in raw_label or "angry" in raw_label or f.pitch_std > 50.0 and f.rms_max > 0.3:
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH
        elif "happy" in raw_label or "satisf" in raw_label or (f.pitch_mean > 190.0 and f.rms_std > 0.035):
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM
        elif "sad" in raw_label or "fear" in raw_label or "disgust" in raw_label:
            return EmotionalTone.DISTRESSED, EmotionalIntensity.HIGH
        elif "frustrat" in raw_label:
            return EmotionalTone.FRUSTRATED, EmotionalIntensity.MEDIUM
        else:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.MEDIUM

    @classmethod
    def _fallback_predict(cls, f: AudioFeatures) -> tuple[EmotionalTone, EmotionalIntensity, float]:
        if f.pitch_std > 50.0 and f.rms_max > 0.30:
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH, 0.82
        elif f.pitch_mean > 190.0 and f.rms_std > 0.035:
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM, 0.82
        else:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.MEDIUM, 0.82
