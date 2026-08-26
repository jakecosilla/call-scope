import time
from typing import Literal

from app.config import CONTAINER_MEMORY_GIB, CPU_COST_PER_SECOND, MEMORY_GIB_COST_PER_SECOND

from app.domain.schema import InternalInferenceMetadata, PredictionResult
from app.inference.approach_a import AcousticPipelineInference
from app.inference.approach_b import SpeechEmotionFoundationInference

PIPELINE_VERSION = "2026-08-27.1"


class InferencePipeline:
    @classmethod
    def analyze_audio(
        cls,
        audio_bytes: bytes,
        filename: str,
        approach: Literal["approach_a", "approach_b"] = "approach_a",
    ) -> tuple[PredictionResult, InternalInferenceMetadata]:
        t0 = time.perf_counter()

        model_name = None
        fallback_used = False
        fallback_reason = None
        if approach == "approach_b":
            prediction, features, preproc_time, infer_time = SpeechEmotionFoundationInference.predict(audio_bytes, filename)
            approach_name = SpeechEmotionFoundationInference.APPROACH_NAME
            model_status = SpeechEmotionFoundationInference.model_status()
            model_name = str(model_status["model_name"])
            fallback_used = bool(model_status["fallback_used"])
            fallback_reason = str(model_status["fallback_reason"]) if model_status["fallback_reason"] else None
        else:
            prediction, features, preproc_time, infer_time = AcousticPipelineInference.predict(
                audio_bytes, filename
            )
            approach_name = AcousticPipelineInference.APPROACH_NAME

        t1 = time.perf_counter()
        total_duration = t1 - t0

        audio_duration = features.duration_seconds if features.duration_seconds > 0 else 1.0
        rtf = total_duration / audio_duration

        estimated_cost_usd = total_duration * (CPU_COST_PER_SECOND + MEMORY_GIB_COST_PER_SECOND * CONTAINER_MEMORY_GIB)
        audio_minutes = audio_duration / 60.0
        cost_per_audio_minute = estimated_cost_usd / audio_minutes if audio_minutes > 0 else 0.0

        metadata = InternalInferenceMetadata(
            pipeline_version=PIPELINE_VERSION,
            approach=approach_name,
            requested_approach=approach,
            model_name=model_name,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            preprocessing_duration_seconds=round(preproc_time, 4),
            inference_duration_seconds=round(infer_time, 4),
            total_duration_seconds=round(total_duration, 4),
            real_time_factor=round(rtf, 4),
            audio_duration_seconds=round(audio_duration, 2),
            estimated_cost_usd=round(estimated_cost_usd, 6),
            estimated_cost_per_audio_minute_usd=round(cost_per_audio_minute, 6),
            raw_acoustic_features={
                "snr_db": round(features.snr_db, 2),
                "pitch_mean_hz": round(features.pitch_mean, 2),
                "pitch_std_hz": round(features.pitch_std, 2),
                "rms_mean": round(features.rms_mean, 4),
                "clipping_ratio": round(features.clipping_ratio, 4),
            },
        )

        return prediction, metadata
