import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.inference.pipeline import InferencePipeline

ASSESSMENT_DIR = os.path.abspath("Software Engineer Assessment")
calls = ["call_001.ogg", "call_002.ogg", "call_003.ogg"]

print("=== CALLSCOPE ASSESSMENT CALLS BENCHMARK ===")

for call_file in calls:
    filepath = os.path.join(ASSESSMENT_DIR, call_file)
    with open(filepath, "rb") as f:
        audio_bytes = f.read()

    pred, meta = InferencePipeline.analyze_audio(audio_bytes, call_file, approach="approach_a")
    print(f"\n[File: {call_file}]")
    print(f"Prediction: {pred.model_dump_json()}")
    print(f"Audio Duration: {meta.audio_duration_seconds}s | Process Time: {meta.total_duration_seconds}s | RTF: {meta.real_time_factor}")
    print(f"Estimated Cost / Min: ${meta.estimated_cost_per_audio_minute_usd:.6f}")

print("\n=== BENCHMARK COMPLETE ===")
