import csv
import io
import json
from typing import Any

from app.domain.schema import PredictionResult

class ManifestValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))

class ModelEvaluator:
    @staticmethod
    def parse_manifest(manifest_content: str) -> dict[str, PredictionResult]:
        ground_truth: dict[str, PredictionResult] = {}
        errors: list[str] = []
        reader = csv.DictReader(io.StringIO(manifest_content))
        if not reader.fieldnames or "name" not in reader.fieldnames:
            raise ManifestValidationError(["labels.csv must contain a 'name' column"])
        for row_number, row in enumerate(reader, start=2):
            filename = (row.get("name") or "").strip()
            result_json = (row.get("result_json") or "").strip()
            if not filename:
                errors.append(f"row {row_number}: missing name")
                continue
            if filename in ground_truth:
                errors.append(f"row {row_number}: duplicate name '{filename}'")
                continue
            if not result_json:
                continue
            try:
                ground_truth[filename] = PredictionResult.model_validate(json.loads(result_json))
            except Exception as exc:
                errors.append(f"row {row_number} ({filename}): invalid result_json ({exc})")
        if errors:
            raise ManifestValidationError(errors)
        return ground_truth

    @classmethod
    def evaluate(cls, predictions: dict[str, PredictionResult], ground_truth: dict[str, PredictionResult]) -> dict[str, Any]:
        keys = sorted(set(predictions) & set(ground_truth))
        if not keys:
            return {"status": "no_matching_files", "total_evaluated": 0}
        tone_classes = ["neutral", "satisfied", "frustrated", "upset", "distressed"]
        matrix = {t: {p: 0 for p in tone_classes} for t in tone_classes}
        true_tones, pred_tones = [], []
        counters = {k: 0 for k in ("emotional_intensity_accuracy","background_noise_present_accuracy","background_noise_type_accuracy","background_noise_severity_accuracy","audio_quality_accuracy","speaker_overlap_accuracy","long_silence_accuracy")}
        for name in keys:
            pred, gt = predictions[name], ground_truth[name]
            true_tones.append(gt.emotional_tone.value); pred_tones.append(pred.emotional_tone.value)
            matrix[gt.emotional_tone.value][pred.emotional_tone.value] += 1
            counters["emotional_intensity_accuracy"] += pred.emotional_intensity == gt.emotional_intensity
            counters["background_noise_present_accuracy"] += pred.background_noise_present == gt.background_noise_present
            counters["background_noise_type_accuracy"] += pred.background_noise_type.strip().casefold() == gt.background_noise_type.strip().casefold()
            counters["background_noise_severity_accuracy"] += pred.background_noise_severity == gt.background_noise_severity
            counters["audio_quality_accuracy"] += pred.audio_quality == gt.audio_quality
            counters["speaker_overlap_accuracy"] += pred.speaker_overlap_present == gt.speaker_overlap_present
            counters["long_silence_accuracy"] += pred.long_silence_present == gt.long_silence_present
        labels = sorted(set(true_tones) | set(pred_tones))
        per_class, f1s = {}, []
        for label in labels:
            tp=sum(t==label and p==label for t,p in zip(true_tones,pred_tones)); fp=sum(t!=label and p==label for t,p in zip(true_tones,pred_tones)); fn=sum(t==label and p!=label for t,p in zip(true_tones,pred_tones))
            precision=tp/(tp+fp) if tp+fp else 0.0; recall=tp/(tp+fn) if tp+fn else 0.0; f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
            f1s.append(f1); per_class[label]={"precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4),"support":sum(t==label for t in true_tones)}
        n=len(keys)
        result={"status":"completed","total_evaluated":n,"emotional_tone_accuracy":round(sum(t==p for t,p in zip(true_tones,pred_tones))/n,4),"emotional_tone_macro_f1":round(sum(f1s)/len(f1s),4) if f1s else 0.0,"per_class_metrics":per_class,"confusion_matrix":matrix,"sample_size_note":"Validation set size is very small; metrics are descriptive, not statistically conclusive."}
        result.update({k:round(v/n,4) for k,v in counters.items()})
        return result
