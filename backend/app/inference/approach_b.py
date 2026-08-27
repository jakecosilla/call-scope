from __future__ import annotations

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
    MODEL_NAME = "superb/wav2vec2-base-superb-er"
    _last_fallback_reason = None
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

                model_name = cls.MODEL_NAME
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
        cls._last_fallback_reason = None

        if model and processor:
            try:
                if sr != 16000:
                    y_16k = librosa.resample(y, orig_sr=sr, target_sr=16000)
                else:
                    y_16k = y

                # Windowed chunk inference for long audio clips (>30s) to limit memory overhead
                if len(y_16k) > 16000 * 30:
                    chunk_samples = 16000 * 15
                    all_probs = []
                    for i in range(0, len(y_16k), chunk_samples):
                        chunk = y_16k[i : i + chunk_samples]
                        if len(chunk) > 16000 * 2:
                            inputs = processor(chunk, sampling_rate=16000, return_tensors="pt", padding=True)
                            with torch.no_grad():
                                logits = model(**inputs).logits
                                chunk_probs = torch.softmax(logits, dim=-1).squeeze().numpy()
                                all_probs.append(chunk_probs)
                    if all_probs:
                        probs = np.mean(all_probs, axis=0)
                    else:
                        inputs = processor(y_16k[: 16000 * 15], sampling_rate=16000, return_tensors="pt", padding=True)
                        with torch.no_grad():
                            logits = model(**inputs).logits
                            probs = torch.softmax(logits, dim=-1).squeeze().numpy()
                else:
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
                logger.error("Inference error in Wav2Vec2 model")
                cls._last_fallback_reason = f"inference_failed:{type(ex).__name__}"
                tone, intensity, confidence_score = cls._fallback_predict(features)
        else:
            cls._last_fallback_reason = f"model_load_failed:{cls._load_error or 'unknown'}"
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
    def model_status(cls) -> dict[str, object | None]:
        return {"model_name": cls.MODEL_NAME, "model_loaded": cls._model is not None, "fallback_used": cls._last_fallback_reason is not None, "fallback_reason": cls._last_fallback_reason}

    @classmethod
    def _map_label_to_enum(cls, raw_label: str, f: AudioFeatures) -> tuple[EmotionalTone, EmotionalIntensity]:
        pitch_var = f.pitch_std_local if f.pitch_std_local > 0 else f.pitch_std
        if "ang" in raw_label or (pitch_var > 50.0 and f.rms_max > 0.30):
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH
        elif "hap" in raw_label or "satisf" in raw_label or (140.0 <= f.pitch_mean <= 170.0 and pitch_var < 48.0):
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM
        elif "sad" in raw_label or "fea" in raw_label or "dis" in raw_label:
            return EmotionalTone.DISTRESSED, EmotionalIntensity.HIGH
        elif "fru" in raw_label:
            return EmotionalTone.FRUSTRATED, EmotionalIntensity.MEDIUM
        else:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.MEDIUM

    @classmethod
    def _fallback_predict(cls, f: AudioFeatures) -> tuple[EmotionalTone, EmotionalIntensity, float]:
        pitch_var = f.pitch_std_local if f.pitch_std_local > 0 else f.pitch_std
        energy_spikes = f.rms_max / (f.rms_mean + 1e-5)

        if pitch_var > 60.0 and f.rms_max > 0.35 and energy_spikes > 6.0:
            return EmotionalTone.DISTRESSED, EmotionalIntensity.HIGH, 0.85

        if pitch_var > 50.0 and f.rms_max > 0.32:
            return EmotionalTone.UPSET, EmotionalIntensity.HIGH, 0.84

        if 185.0 <= f.pitch_mean <= 205.0 and pitch_var < 52.0:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.MEDIUM, 0.82

        if 140.0 <= f.pitch_mean <= 170.0 and pitch_var < 48.0:
            return EmotionalTone.SATISFIED, EmotionalIntensity.MEDIUM, 0.82

        if f.pitch_mean > 205.0 and pitch_var < 52.0:
            return EmotionalTone.NEUTRAL, EmotionalIntensity.MEDIUM, 0.82

        return EmotionalTone.NEUTRAL, EmotionalIntensity.LOW, 0.75
