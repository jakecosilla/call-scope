import logging
import time

import librosa
import numpy as np
import torch

from app.audio.processor import AudioFeatures, AudioProcessor
from app.domain.schema import (
    EmotionalIntensity,
    EmotionalTone,
    PredictionResult,
)

logger = logging.getLogger(__name__)


class SpeechEmotionFoundationInference:
    APPROACH_NAME = "Foundation SER Model"
    _model = None
    _processor = None
    _load_attempted = False
    _load_error = None

    @classmethod
    def _get_model(cls):
        if not cls._load_attempted:
            cls._load_attempted = True
            try:
                from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

                model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
                cls._processor = AutoFeatureExtractor.from_pretrained(model_name)
                cls._model = AutoModelForAudioClassification.from_pretrained(model_name)
                cls._model.eval()
                logger.info("Successfully loaded Foundation Wav2Vec2 SER model")
            except Exception as ex:
                cls._model = None
                cls._load_error = str(ex)
                logger.warning(f"Foundation model load failed (using acoustic fallback): {ex}")
        return cls._model, cls._processor

    @classmethod
    def predict(
        cls, audio_bytes: bytes, filename: str
    ) -> tuple[PredictionResult, AudioFeatures, float, float]:
        t0 = time.perf_counter()
        y, sr = AudioProcessor.load_audio(audio_bytes, filename)
        features = AudioProcessor.extract_features(y, sr)
        t1 = time.perf_counter()

        model, processor = cls._get_model()

        if model and processor:
            try:
                if sr != 16000:
                    y_16k = librosa.resample(y, orig_sr=sr, target_sr=16000)
                else:
                    y_16k = y

                inputs = processor(y_16k, sampling_rate=16000, return_tensors="pt", padding=True)
                with torch.no_grad():
                    logits = model(**inputs).logits
                    probs = torch.softmax(logits, dim=-1).squeeze().numpy()

                label_id = int(np.argmax(probs))
                confidence_score = float(probs[label_id])

                id2label = getattr(model.config, "id2label", {})
                raw_label = str(id2label.get(label_id, "neutral")).lower()

                tone, intensity = cls._map_label_to_enum(raw_label, features)
            except Exception as ex:
                logger.error(f"Inference error in Wav2Vec2 model: {ex}")
                tone, intensity, confidence_score = cls._fallback_predict(features)
        else:
            tone, intensity, confidence_score = cls._fallback_predict(features)

        t2 = time.perf_counter()
        confidence = float(max(0.35, min(0.98, round(confidence_score, 2))))

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
    def _map_label_to_enum(cls, raw_label: str, f: AudioFeatures) -> tuple[EmotionalTone, EmotionalIntensity]:
        if "angry" in raw_label or (f.pitch_std > 50.0 and f.rms_max > 0.3):
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH
        elif "happy" in raw_label or "satisf" in raw_label:
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM
        elif "sad" in raw_label or "fear" in raw_label or "disgust" in raw_label:
            return EmotionalTone.DISTRESSED, EmotionalIntensity.HIGH
        elif "frustrat" in raw_label:
            return EmotionalTone.FRUSTRATED, EmotionalIntensity.MEDIUM
        else:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.LOW

    @classmethod
    def _fallback_predict(cls, f: AudioFeatures) -> tuple[EmotionalTone, EmotionalIntensity, float]:
        if f.pitch_std > 50.0 and f.rms_max > 0.30:
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH, 0.78
        elif f.pitch_mean > 190.0 and f.rms_std > 0.035:
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM, 0.75
        else:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.LOW, 0.70
