import numpy as np
import pytest

from app.audio.processor import AudioProcessor
from app.domain.schema import AudioQuality


def test_audio_processor_extract_features_synthetic_sine():
    sr = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    features = AudioProcessor.extract_features(y, sr)
    assert features.duration_seconds == pytest.approx(2.0, abs=0.01)
    assert features.audio_quality == AudioQuality.CLEAR
    assert features.clipping_ratio == 0.0
    assert features.long_silence_present is False


def test_audio_processor_clipping_detection():
    sr = 16000
    duration = 1.0
    y = np.ones(int(sr * duration), dtype=np.float32)

    features = AudioProcessor.extract_features(y, sr)
    assert features.clipping_ratio == 1.0
    assert features.audio_quality == AudioQuality.SEVERELY_IMPAIRED
