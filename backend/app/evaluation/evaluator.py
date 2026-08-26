import csv
import io
import json
from typing import Any

import numpy as np

from app.domain.schema import PredictionResult


class ModelEvaluator:
    @staticmethod
    def parse_manifest(manifest_content: str) -> dict[str, PredictionResult]:
        ground_truth = {}
        reader = csv.DictReader(io.StringIO(manifest_content))
        for row in reader:
            filename = row.get("name", "").strip()
            result_json_str = row.get("result_json", "").strip()
            if filename and result_json_str:
                try:
                    data = json.loads(result_json_str)
                    prediction = PredictionResult.model_validate(data)
                    ground_truth[filename] = prediction
                except Exception:
                    continue
        return ground_truth

    @classmethod
    def evaluate(
        cls,
        predictions: dict[str, PredictionResult],
        ground_truth: dict[str, PredictionResult],
    ) -> dict[str, Any]:
        matched_keys = set(predictions.keys()).intersection(set(ground_truth.keys()))
        if not matched_keys:
            return {"status": "no_matching_files", "total_evaluated": 0}

        tone_correct = 0
        intensity_correct = 0
        noise_present_correct = 0
        noise_severity_correct = 0
        quality_correct = 0
        overlap_correct = 0
        silence_correct = 0

        tone_classes = ["neutral", "satisfied", "frustrated", "upset", "distressed"]
        matrix = {t_true: {t_pred: 0 for t_pred in tone_classes} for t_true in tone_classes}

        class_tp = {c: 0 for c in tone_classes}
        class_fp = {c: 0 for c in tone_classes}
        class_fn = {c: 0 for c in tone_classes}

        for filename in matched_keys:
            pred = predictions[filename]
            gt = ground_truth[filename]

            if pred.emotional_tone.value == gt.emotional_tone.value:
                tone_correct += 1
                class_tp[pred.emotional_tone.value] += 1
            else:
                class_fp[pred.emotional_tone.value] += 1
                class_fn[gt.emotional_tone.value] += 1

            if pred.emotional_tone.value in tone_classes and gt.emotional_tone.value in tone_classes:
                matrix[gt.emotional_tone.value][pred.emotional_tone.value] += 1

            if pred.emotional_intensity.value == gt.emotional_intensity.value:
                intensity_correct += 1
            if pred.background_noise_present == gt.background_noise_present:
                noise_present_correct += 1
            if pred.background_noise_severity.value == gt.background_noise_severity.value:
                noise_severity_correct += 1
            if pred.audio_quality.value == gt.audio_quality.value:
                quality_correct += 1
            if pred.speaker_overlap_present == gt.speaker_overlap_present:
                overlap_correct += 1
            if pred.long_silence_present == gt.long_silence_present:
                silence_correct += 1

        n = len(matched_keys)

        per_class_metrics = {}
        f1_scores = []
        for c in tone_classes:
            tp = class_tp[c]
            fp = class_fp[c]
            fn = class_fn[c]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            per_class_metrics[c] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": tp + fn,
            }
            if (tp + fn) > 0 or (tp + fp) > 0:
                f1_scores.append(f1)

        macro_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0

        return {
            "status": "completed",
            "total_evaluated": n,
            "emotional_tone_accuracy": round(tone_correct / n, 4),
            "emotional_tone_macro_f1": round(macro_f1, 4),
            "emotional_intensity_accuracy": round(intensity_correct / n, 4),
            "background_noise_present_accuracy": round(noise_present_correct / n, 4),
            "background_noise_severity_accuracy": round(noise_severity_correct / n, 4),
            "audio_quality_accuracy": round(quality_correct / n, 4),
            "speaker_overlap_accuracy": round(overlap_correct / n, 4),
            "long_silence_accuracy": round(silence_correct / n, 4),
            "per_class_metrics": per_class_metrics,
            "confusion_matrix": matrix,
            "sample_size_note": "Validation set size is 3 calls. Statistical significance is indicative.",
        }
