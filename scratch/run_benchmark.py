import io
import math
import os
import platform
import sys
import wave
from typing import Literal

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.evaluation.evaluator import ModelEvaluator
from app.inference.pipeline import InferencePipeline


def generate_synthetic_audio_bytes(duration_seconds: float = 5.0, sample_rate: int = 16000) -> bytes:
    num_samples = int(duration_seconds * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            val = int(32767.0 * 0.2 * math.sin(2 * math.pi * 440.0 * i / sample_rate))
            frames.extend(val.to_bytes(2, byteorder="little", signed=True))
        wf.writeframes(frames)
    return buf.getvalue()


def run_benchmark(approach: Literal["approach_a", "approach_b"] = "approach_a", fail_on_fallback: bool = False):
    assessment_dir = os.path.abspath("Software Engineer Assessment")
    labels_file = os.path.join(assessment_dir, "labels.csv")
    calls = ["call_001.ogg", "call_002.ogg", "call_003.ogg"]

    print("================================================================================")
    print(f"CALLSCOPE REPRODUCIBLE BENCHMARK & ACCURACY REPORT (Approach: {approach})")
    print("================================================================================")
    print(f"System Environment : {platform.platform()} | Python {platform.python_version()}")
    print(f"CPU Architecture   : {platform.machine()} ({os.cpu_count()} vCPUs available)")
    print("================================================================================")

    predictions = {}

    if os.path.exists(assessment_dir) and all(
        os.path.exists(os.path.join(assessment_dir, c)) for c in calls
    ):
        for call_file in calls:
            filepath = os.path.join(assessment_dir, call_file)
            with open(filepath, "rb") as f:
                audio_bytes = f.read()

            pred, meta = InferencePipeline.analyze_audio(audio_bytes, call_file, approach=approach)
            predictions[call_file] = pred
            if fail_on_fallback and meta.fallback_used:
                raise RuntimeError(f"{call_file}: fallback used: {meta.fallback_reason}")

            print(f"\n[File: {call_file}]")
            print(f"Prediction : {pred.model_dump_json()}")
            print(
                f"Timing     : Audio {meta.audio_duration_seconds}s | Preprocess {meta.preprocessing_duration_seconds}s | Inference {meta.inference_duration_seconds}s | Total {meta.total_duration_seconds}s | RTF {meta.real_time_factor}"
            )
            print(f"Est Cost   : ${meta.estimated_cost_per_audio_minute_usd:.6f} / audio minute")

        if os.path.exists(labels_file):
            with open(labels_file, "r", encoding="utf-8") as f:
                manifest_content = f.read()

            ground_truth = ModelEvaluator.parse_manifest(manifest_content)
            metrics = ModelEvaluator.evaluate(predictions, ground_truth)

            print("\n--------------------------------------------------------------------------------")
            print("GROUND TRUTH EVALUATION METRICS:")
            print("--------------------------------------------------------------------------------")
            print(f"Total Clips Evaluated       : {metrics.get('total_evaluated', 0)}")
            print(f"Emotional Tone Accuracy     : {metrics.get('emotional_tone_accuracy', 0.0) * 100:.1f}%")
            print(f"Emotional Tone Macro F1     : {metrics.get('emotional_tone_macro_f1', 0.0):.4f}")
            print(f"Emotional Intensity Acc     : {metrics.get('emotional_intensity_accuracy', 0.0) * 100:.1f}%")
            print(f"Background Noise Present Acc: {metrics.get('background_noise_present_accuracy', 0.0) * 100:.1f}%")
            print(f"Background Noise Type Acc   : {metrics.get('background_noise_type_accuracy', 0.0) * 100:.1f}%")
            print(f"Background Noise Severity Acc: {metrics.get('background_noise_severity_accuracy', 0.0) * 100:.1f}%")
            print(f"Audio Quality Accuracy      : {metrics.get('audio_quality_accuracy', 0.0) * 100:.1f}%")
            print(f"Speaker Overlap Accuracy    : {metrics.get('speaker_overlap_accuracy', 0.0) * 100:.1f}%")
            print(f"Long Silence Accuracy       : {metrics.get('long_silence_accuracy', 0.0) * 100:.1f}%")
            print("--------------------------------------------------------------------------------")
            print("Confusion Matrix (Emotional Tone):")
            print(metrics.get("confusion_matrix", {}))
            print("--------------------------------------------------------------------------------")
    else:
        print("\n[INFO] Assessment fixtures directory not found. Running synthetic audio benchmark...")
        synthetic_bytes = generate_synthetic_audio_bytes(duration_seconds=5.0)
        pred, meta = InferencePipeline.analyze_audio(
            synthetic_bytes, "synthetic_test_call.wav", approach=approach
        )
        print("\n[File: synthetic_test_call.wav]")
        print(f"Prediction : {pred.model_dump_json()}")
        print(
            f"Timing     : Preprocess {meta.preprocessing_duration_seconds}s | Inference {meta.inference_duration_seconds}s | Total {meta.total_duration_seconds}s | RTF {meta.real_time_factor}"
        )
        print(f"Est Cost   : ${meta.estimated_cost_per_audio_minute_usd:.6f} / audio minute")

    print("\n=== BENCHMARK COMPLETE ===")


if __name__ == "__main__":
    appr = "approach_a"
    if "--approach" in sys.argv:
        idx = sys.argv.index("--approach")
        if idx + 1 < len(sys.argv):
            appr = sys.argv[idx + 1]
    run_benchmark(approach=appr, fail_on_fallback="--fail-on-fallback" in sys.argv)
