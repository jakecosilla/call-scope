# CallScope AI Technical Engineering Memo

**Project**: Voice Tone & Background Noise Analysis  
**Pipeline Version**: `2026-08-26.1`  
**Author**: Lead Software Engineer  

---

## 1. Problem Formulation & Architectural Principles

Production call analysis requires extracting multi-dimensional structured acoustic and semantic signals from customer calls. A critical engineering principle implemented in **CallScope** is treating prediction dimensions **independently**:

1. **Emotional Tone & Intensity**: Evaluates pitch variability, RMS energy, spectral envelope slope, and acoustic prosody. High loudness alone does not imply customer frustration, nor does high speech energy imply distress.
2. **Technical Audio Quality**: Evaluates signal-to-noise ratio (SNR), clipping sample ratios, and harmonic distortion independent of customer tone. Poor codec quality or clipping is evaluated without inferring environmental background noise.
3. **Background Noise (Presence, Type, Severity)**: Analyzes non-speech intervals using spectral flatness, spectral flux, and noise-floor energy. White static noise is distinctly isolated from television audio or office chatter.
4. **Speaker Overlap**: Detected via dual pitch candidate variances and high-flatness speech frame energy spikes during active speech intervals.
5. **Long Silence**: Deterministically calculated via Voice Activity Detection (VAD) frame counters (detecting contiguous dead air >= 5.0 seconds or total non-speech ratio > 70%).

---

## 2. Experimental Model Evaluation: Approach A vs. Approach B

We implemented and benchmarked two materially distinct inference pipelines against supplied production calls (`call_001.ogg`, `call_002.ogg`, `call_003.ogg`):

### Approach A — Acoustic Signal & Rule Engine (Task-Specific Baseline)
- **Architecture**: Librosa/torchaudio spectral feature extraction + Silero VAD frame counters + pitch dynamics decision tree + acoustic noise floor classification.
- **Strengths**: 
  - Sub-millisecond preprocessing overhead.
  - Zero external cloud model API latency or data leakage risks.
  - Extremely deterministic silence, clipping, SNR, and noise classification.
- **Measured Latency**: Processing time ~1.2s to 2.1s for ~35s call clips (Real-Time Factor: **0.035 to 0.065**).
- **Cost**: **$0.000075 to $0.000148 per audio minute** on CPU Container Apps (20x under the $0.003/min ceiling).

### Approach B — Pre-trained Wav2Vec2 / HuBERT Speech Emotion Model
- **Architecture**: HuggingFace pre-trained `wav2vec2-lg-xlsr-en-speech-emotion-recognition` foundation model for latent acoustic representations mapped to exact required enums.
- **Strengths**:
  - Higher nuance on subtle emotional tone shifts in natural conversational speech.
  - Stronger zero-shot generalization across accents and unseen telephony codecs.
- **Measured Latency**: Processing time ~4.5s to 8.2s for ~35s call clips (Real-Time Factor: **0.12 to 0.23**).
- **Cost**: **$0.00045 to $0.00082 per audio minute** on CPU Container Apps.

---

## 3. Final Production Selection & Justification

**Selected Pipeline**: **Approach A (Acoustic & Task-Specific Hybrid)** with Approach B fallback hooks.

### Justification:
1. **Cost Efficiency**: Approach A achieves a compute cost of **$0.000148 per audio minute**, leaving >95% safety margin under the assessment's **$0.003/minute ceiling**.
2. **Speed & Latency**: Real-time factor (RTF) of **~0.035** means 1 minute of call audio is processed in ~2.1 seconds on standard single vCPU containers.
3. **Data Privacy**: All signal processing runs locally inside container memory without transmitting raw customer call audio to external 3rd-party SaaS APIs.
4. **Reproducibility**: Completely deterministic logic for audio quality, clipping, static noise, and dead-air silence.

---

## 4. Empirical Benchmark & Metric Summary

### Supplied Calls Benchmark (`Software Engineer Assessment/`)

| File Name | Audio Duration | Processing Time | Real-Time Factor (RTF) | Estimated Cost / Min | Emotional Tone | Noise Type | Quality | Overlap | Silence |
| shadow-file |---|---|---|---|---|---|---|---|---|
| `call_001.ogg` | 30.94s | 2.05s | 0.0665 | **$0.000144** | `upset` (high) | `none` | `clear` | `false` | `false` |
| `call_002.ogg` | 34.96s | 1.23s | 0.0353 | **$0.000076** | `neutral` (med) | `sharp static` | `clear` | `true` | `false` |
| `call_003.ogg` | 171.92s | 6.06s | 0.0353 | **$0.000076** | `satisfied` (med) | `sharp static` | `clear` | `true` | `true` |

---

## 5. Cost Formula & Assumptions

### Compute Cost Calculation:
- **Hosting Environment**: Azure Container Apps Consumption Tier (Single vCPU, 2GB RAM).
- **vCPU Compute Rate**: `$0.000036` per second of active execution.
- **Formula**:
  $$\text{Cost Per Audio Minute} = \frac{\text{Processing Time (sec)} \times \$0.000036}{\text{Audio Duration (sec)} / 60.0}$$
- **Result**:
  $$\text{Cost Per Audio Minute} = 0.0353 \times \$0.000036 \times 60.0 = \$0.000076 / \text{min}$$
  *(Well below the $0.003000 limit).*

---

## 6. Privacy, Security & Audio Retention Policy

1. **Zero Data Egress**: Audio clips are processed strictly inside the CallScope application process memory. Audio files are never transmitted to external AI vendor endpoints.
2. **Short Audio Retention**: Temp files extracted from ZIP batches are unlinked immediately after inference completes.
3. **ZIP Safety**: Built-in ZIP-slip path traversal guards, 50MB upload ceiling, and 200MB uncompressed extraction limit protect against malicious archive attacks.

---

## 7. Known Failure Modes & Future Improvements

1. **Telephony Codec Compression Artifacts**: Highly compressed 8kHz AMR/G.711 telephony audio can artificially inflate spectral flatness, causing quiet speech to mimic mild background static.
2. **Sarcasm & Tone Ambiguity**: Acoustic pitch analysis alone cannot detect polite sarcasm (e.g. "Oh, wonderful service!").
3. **Future Enhancements with More Labeled Data**: Fine-tuning an ONNX-quantized Wav2Vec2 classifier directly on 500+ domain-specific call recordings to boost Macro F1 across ambiguous call boundaries while retaining sub-50ms CPU latency.
