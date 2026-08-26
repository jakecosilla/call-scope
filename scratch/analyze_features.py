import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.audio.processor import AudioProcessor

ASSESSMENT_DIR = os.path.abspath("Software Engineer Assessment")
calls = ["call_001.ogg", "call_002.ogg", "call_003.ogg"]

for filename in calls:
    filepath = os.path.join(ASSESSMENT_DIR, filename)
    with open(filepath, "rb") as f:
        audio_bytes = f.read()

    y, sr = AudioProcessor.load_audio(audio_bytes, filename)
    feat = AudioProcessor.extract_features(y, sr)
    print(f"\n--- {filename} ---")
    print(f"Duration: {feat.duration_seconds:.2f}s | SNR: {feat.snr_db:.2f}dB | SpeechRatio: {feat.speech_ratio:.2f}")
    print(f"RMS Mean: {feat.rms_mean:.4f} | RMS Max: {feat.rms_max:.4f} | Flatness: {feat.spectral_flatness_mean:.6f}")
    print(f"Centroid Mean: {feat.spectral_centroid_mean:.1f}Hz | Pitch Mean: {feat.pitch_mean:.1f}Hz | Pitch Std: {feat.pitch_std:.1f}Hz")
    print(f"Detected Noise: present={feat.background_noise_present}, type='{feat.background_noise_type}', sev='{feat.background_noise_severity.value}'")
    print(f"Detected Overlap: {feat.speaker_overlap_present} | Silence: {feat.long_silence_present}")
