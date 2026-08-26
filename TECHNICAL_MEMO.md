# CallScope Technical Engineering Memo

**Pipeline version:** `2026-08-27.1`

## Problem
The service predicts emotional tone/intensity, background-noise presence/type/severity, audio quality, speaker overlap, long silence, and confidence. These dimensions are treated independently where practical.

## Approach A — Acoustic Signal Engine
Uses RMS, pitch statistics, clipping, SNR/noise-floor features, spectral flatness/centroid and continuous-silence analysis. Emotion/noise/overlap mappings remain heuristic and must be validated on a larger independent dataset; the three supplied calls are insufficient to calibrate production thresholds.

## Approach B — Foundation SER
Uses `superb/wav2vec2-base-superb-er` at 16 kHz. Long audio is chunked and chunk probabilities are averaged. Runtime mode can fall back to acoustic inference, but benchmark mode can fail on fallback so results are not misattributed.

## Validation
Run `python scratch/run_benchmark.py --approach approach_a` and `python scratch/run_benchmark.py --approach approach_b --fail-on-fallback`. Benchmark output is the source of truth for accuracy, emotional-tone macro F1, confusion matrix, latency and cost. The evaluator also measures background-noise-type exact-match accuracy. Do not publish stale manually entered benchmark values.

## Cost
Configured estimate: `processing_seconds * (vCPU_cost_per_second + memory_GiB_cost_per_second * container_memory_GiB)`. Free-tier grants are not used to prove intrinsic inference cost.

## Privacy
Customer audio is not sent to a third-party inference API. Foundation-model artifacts may be downloaded during provisioning/startup unless pre-baked or stored in controlled infrastructure.

## Reliability
CPU inference is moved off the FastAPI event loop and concurrency bounded. Batch metadata uses configurable SQLite storage; a container-local SQLite file is not sufficient for multi-replica Azure durability, so production should use durable mounted or managed storage. In-flight restart recovery also requires durable audio staging.

## Known Limitations
- acoustic thresholds require independent validation
- overlap detection is heuristic rather than full diarization
- three labeled calls do not establish statistical significance
- hosted Azure pipelines must still be executed and smoke-tested with real infrastructure
