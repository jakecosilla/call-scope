import io
from dataclasses import dataclass, field

import librosa
import numpy as np
import soundfile as sf  # type: ignore[import-untyped]

from app.domain.schema import AudioQuality, BackgroundNoiseSeverity


@dataclass
class AudioFeatures:
    duration_seconds: float
    sample_rate: int
    num_channels: int
    rms_mean: float
    rms_std: float
    rms_max: float
    snr_db: float
    clipping_ratio: float
    spectral_flatness_mean: float
    spectral_centroid_mean: float
    pitch_mean: float
    pitch_std: float
    pitch_std_local: float = 0.0
    pitch_contour: list[float] = field(default_factory=list)
    speech_ratio: float = 0.0
    long_silence_present: bool = False
    audio_quality: AudioQuality = AudioQuality.CLEAR
    background_noise_present: bool = False
    background_noise_type: str = ""
    background_noise_severity: BackgroundNoiseSeverity = BackgroundNoiseSeverity.NONE
    speaker_overlap_present: bool = False


class AudioProcessor:
    @staticmethod
    def load_audio(file_bytes: bytes, filename: str) -> tuple[np.ndarray, int]:
        try:
            audio_buf = io.BytesIO(file_bytes)
            y, sr = sf.read(audio_buf, dtype="float32")
            if y.ndim > 1:
                y = np.mean(y, axis=1)
            return y, int(sr)
        except Exception:
            audio_buf = io.BytesIO(file_bytes)
            y, sr = librosa.load(audio_buf, sr=16000, mono=True)
            return y, int(sr)

    @classmethod
    def extract_features(cls, y: np.ndarray, sr: int) -> AudioFeatures:
        if len(y) == 0:
            raise ValueError("Empty audio signal")

        duration = float(len(y) / sr)
        abs_y = np.abs(y)
        clipping_samples = np.sum(abs_y >= 0.98)
        clipping_ratio = float(clipping_samples / len(y))

        frame_length = int(sr * 0.03)
        hop_length = int(sr * 0.01)

        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        rms_mean = float(np.mean(rms))
        rms_std = float(np.std(rms))
        rms_max = float(np.max(rms))

        spectral_flatness = librosa.feature.spectral_flatness(y=y, hop_length=hop_length)[0]
        flatness_mean = float(np.mean(spectral_flatness))

        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
        centroid_mean = float(np.mean(spectral_centroid))

        speech_threshold = max(rms_mean * 0.35, 0.0020)
        is_speech_frame = rms > speech_threshold
        speech_ratio = float(np.mean(is_speech_frame))

        # Long silence: Require at least 8.0 continuous seconds of uninterrupted dead air
        consecutive_silent_frames = 0
        max_silent_frames = 0
        silence_frame_threshold = int(8.0 / (hop_length / sr))

        for is_speech in is_speech_frame:
            if not is_speech:
                consecutive_silent_frames += 1
                if consecutive_silent_frames > max_silent_frames:
                    max_silent_frames = consecutive_silent_frames
            else:
                consecutive_silent_frames = 0

        long_silence_present = bool(max_silent_frames >= silence_frame_threshold)

        non_speech_mask = ~is_speech_frame
        if np.any(non_speech_mask) and np.any(is_speech_frame):
            speech_power = np.mean(rms[is_speech_frame] ** 2) + 1e-9
            noise_power = np.mean(rms[non_speech_mask] ** 2) + 1e-9
            snr_db = float(10 * np.log10(speech_power / noise_power))
        else:
            snr_db = 30.0

        if clipping_ratio > 0.05 or snr_db < 3.0:
            quality = AudioQuality.SEVERELY_IMPAIRED
        elif clipping_ratio > 0.01 or snr_db < 10.0:
            quality = AudioQuality.SLIGHTLY_IMPAIRED
        else:
            quality = AudioQuality.CLEAR

        non_speech_flatness = (
            float(np.mean(spectral_flatness[non_speech_mask]))
            if np.any(non_speech_mask)
            else flatness_mean
        )
        non_speech_rms = (
            float(np.mean(rms[non_speech_mask])) if np.any(non_speech_mask) else 0.0
        )
        non_speech_centroid = (
            float(np.mean(spectral_centroid[non_speech_mask]))
            if np.any(non_speech_mask)
            else centroid_mean
        )

        noise_present = False
        noise_type = ""
        noise_severity = BackgroundNoiseSeverity.NONE

        if snr_db < 28.0 or non_speech_rms > 0.0022 or non_speech_flatness > 0.0035:
            noise_present = True
            if non_speech_flatness > 0.0040:
                noise_type = "TV"
                noise_severity = BackgroundNoiseSeverity.MEDIUM
            elif snr_db < 22.0 or non_speech_rms > 0.0030 or (1000.0 <= non_speech_centroid <= 2800.0 and non_speech_flatness < 0.0030):
                noise_type = "sharp static"
                noise_severity = (
                    BackgroundNoiseSeverity.HIGH if snr_db < 10.0 else BackgroundNoiseSeverity.MEDIUM
                )
            elif non_speech_centroid < 800.0:
                noise_type = "road noise"
                noise_severity = BackgroundNoiseSeverity.MEDIUM
            else:
                noise_type = "background noise"
                noise_severity = BackgroundNoiseSeverity.LOW
        else:
            noise_present = False
            noise_type = ""
            noise_severity = BackgroundNoiseSeverity.NONE

        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=float(librosa.note_to_hz("C2")),
            fmax=float(librosa.note_to_hz("C7")),
            sr=sr,
            hop_length=hop_length,
        )
        voiced_f0 = f0[voiced_flag & ~np.isnan(f0)] if f0 is not None else np.array([])
        if len(voiced_f0) > 10:
            pitch_mean = float(np.mean(voiced_f0))
            pitch_std = float(np.std(voiced_f0))
            pitch_contour = voiced_f0.tolist()

            win_size = int(5.0 / (hop_length / sr))
            local_stds = []
            for i in range(0, max(1, len(voiced_f0) - win_size), max(1, win_size // 2)):
                chunk = voiced_f0[i : i + win_size]
                if len(chunk) > 5:
                    local_stds.append(float(np.std(chunk)))
            pitch_std_local = float(np.median(local_stds)) if local_stds else pitch_std
        else:
            pitch_mean = 0.0
            pitch_std = 0.0
            pitch_std_local = 0.0
            pitch_contour = []

        overlap_present = False
        if len(rms) > 10 and np.any(is_speech_frame):
            speech_rms_std = float(np.std(rms[is_speech_frame]))
            if speech_rms_std > 0.042 and pitch_std_local < 52.0:
                overlap_present = True

        return AudioFeatures(
            duration_seconds=duration,
            sample_rate=sr,
            num_channels=1,
            rms_mean=rms_mean,
            rms_std=rms_std,
            rms_max=rms_max,
            snr_db=snr_db,
            clipping_ratio=clipping_ratio,
            spectral_flatness_mean=flatness_mean,
            spectral_centroid_mean=centroid_mean,
            pitch_mean=pitch_mean,
            pitch_std=pitch_std,
            pitch_std_local=pitch_std_local,
            pitch_contour=pitch_contour,
            speech_ratio=speech_ratio,
            long_silence_present=long_silence_present,
            audio_quality=quality,
            background_noise_present=noise_present,
            background_noise_type=noise_type,
            background_noise_severity=noise_severity,
            speaker_overlap_present=overlap_present,
        )
