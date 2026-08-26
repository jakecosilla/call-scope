import asyncio
import csv
import io
import os
import threading
import uuid
import zipfile
from datetime import UTC, datetime
from typing import Literal

from app.domain.schema import CallAnalysisFileResult
from app.evaluation.evaluator import ModelEvaluator
from app.inference.pipeline import InferencePipeline
from app.storage.store import BatchStore

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_SIZE_BYTES = 200 * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3", ".flac", ".m4a", ".aac"}


class BatchProcessor:
    @classmethod
    def process_zip_bytes(
        cls,
        file_bytes: bytes,
        filename: str = "batch.zip",
        approach: Literal["approach_a", "approach_b"] = "approach_a",
    ) -> tuple[str, dict]:
        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"Upload size exceeds maximum allowed limit ({MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB)")

        batch_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        store = BatchStore.get_instance()

        audio_files: dict[str, bytes] = {}
        manifest_content: str | None = None
        total_uncompressed_bytes = 0

        ext = os.path.splitext(filename)[1].lower() if filename else ""

        if ext == ".zip" or zipfile.is_zipfile(io.BytesIO(file_bytes)):
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
                for member in zf.infolist():
                    if member.is_dir():
                        continue

                    clean_name = os.path.basename(member.filename)
                    if not clean_name or clean_name.startswith(".") or ".." in member.filename:
                        continue

                    total_uncompressed_bytes += member.file_size
                    if total_uncompressed_bytes > MAX_UNCOMPRESSED_SIZE_BYTES:
                        raise ValueError("Extracted batch size exceeds maximum safety limit")

                    member_ext = os.path.splitext(clean_name)[1].lower()

                    if clean_name.lower() == "labels.csv" or member_ext == ".csv":
                        manifest_content = zf.read(member).decode("utf-8", errors="ignore")
                    elif member_ext in ALLOWED_AUDIO_EXTENSIONS:
                        audio_files[clean_name] = zf.read(member)
        elif ext in ALLOWED_AUDIO_EXTENSIONS:
            clean_name = os.path.basename(filename)
            audio_files[clean_name] = file_bytes
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. Please upload audio clips (.ogg, .wav, .mp3) or a .zip archive."
            )

        if not audio_files:
            raise ValueError("No supported audio files found in upload")

        store.create_batch(batch_id, total_files=len(audio_files), created_at=created_at)

        manifest_validation = {}
        if manifest_content:
            ground_truth = ModelEvaluator.parse_manifest(manifest_content)
            store.set_ground_truth(batch_id, ground_truth)
            manifest_validation = cls._validate_manifest(list(audio_files.keys()), manifest_content)

        cls._schedule_batch_processing(batch_id, audio_files, approach)

        return batch_id, manifest_validation

    @classmethod
    def _schedule_batch_processing(
        cls,
        batch_id: str,
        audio_files: dict[str, bytes],
        approach: Literal["approach_a", "approach_b"],
    ):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(cls._run_batch_async(batch_id, audio_files, approach))
        except RuntimeError:
            thread = threading.Thread(
                target=lambda: asyncio.run(cls._run_batch_async(batch_id, audio_files, approach)),
                daemon=True,
            )
            thread.start()

    @classmethod
    def _validate_manifest(cls, audio_filenames: list[str], manifest_content: str) -> dict:
        matched = []
        unmatched_audio = []
        missing_audio = []
        duplicate_names = []

        reader = csv.DictReader(io.StringIO(manifest_content))
        manifest_names = []
        for row in reader:
            name = row.get("name", "").strip()
            if name:
                if name in manifest_names:
                    duplicate_names.append(name)
                manifest_names.append(name)

        audio_set = set(audio_filenames)
        manifest_set = set(manifest_names)

        matched = list(audio_set.intersection(manifest_set))
        unmatched_audio = list(audio_set - manifest_set)
        missing_audio = list(manifest_set - audio_set)

        return {
            "total_manifest_rows": len(manifest_names),
            "matched_files": len(matched),
            "unmatched_audio_files": unmatched_audio,
            "missing_audio_files": missing_audio,
            "duplicate_manifest_rows": duplicate_names,
        }

    @classmethod
    async def _run_batch_async(
        cls,
        batch_id: str,
        audio_files: dict[str, bytes],
        approach: Literal["approach_a", "approach_b"],
    ):
        store = BatchStore.get_instance()
        batch = store.get_batch(batch_id)
        if batch:
            batch.status = "processing"

        for filename, audio_bytes in audio_files.items():
            file_id = str(uuid.uuid4())
            try:
                prediction, metadata = await asyncio.to_thread(
                    InferencePipeline.analyze_audio, audio_bytes, filename, approach=approach
                )
                file_result = CallAnalysisFileResult(
                    file_id=file_id,
                    filename=filename,
                    status="completed",
                    prediction=prediction,
                    metadata=metadata,
                )
            except Exception as ex:
                file_result = CallAnalysisFileResult(
                    file_id=file_id,
                    filename=filename,
                    status="failed",
                    error_message=f"Failed to process audio clip: {str(ex)}",
                )
            completed_at = datetime.now(UTC).isoformat()
            store.update_file_result(batch_id, file_result, completed_at=completed_at)
            await asyncio.sleep(0.01)

    @classmethod
    def export_csv(cls, batch_id: str) -> str:
        store = BatchStore.get_instance()
        batch = store.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        output = io.StringIO()
        fieldnames = [
            "name",
            "emotional_tone",
            "emotional_intensity",
            "background_noise_present",
            "background_noise_type",
            "background_noise_severity",
            "audio_quality",
            "speaker_overlap_present",
            "long_silence_present",
            "confidence",
            "status",
            "error_message",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for f in batch.files:
            if f.prediction:
                writer.writerow(
                    {
                        "name": f.filename,
                        "emotional_tone": f.prediction.emotional_tone.value,
                        "emotional_intensity": f.prediction.emotional_intensity.value,
                        "background_noise_present": str(f.prediction.background_noise_present).lower(),
                        "background_noise_type": f.prediction.background_noise_type,
                        "background_noise_severity": f.prediction.background_noise_severity.value,
                        "audio_quality": f.prediction.audio_quality.value,
                        "speaker_overlap_present": str(f.prediction.speaker_overlap_present).lower(),
                        "long_silence_present": str(f.prediction.long_silence_present).lower(),
                        "confidence": f.prediction.confidence,
                        "status": f.status,
                        "error_message": "",
                    }
                )
            else:
                writer.writerow(
                    {
                        "name": f.filename,
                        "emotional_tone": "",
                        "emotional_intensity": "",
                        "background_noise_present": "",
                        "background_noise_type": "",
                        "background_noise_severity": "",
                        "audio_quality": "",
                        "speaker_overlap_present": "",
                        "long_silence_present": "",
                        "confidence": "",
                        "status": f.status,
                        "error_message": f.error_message or "Unknown error",
                    }
                )

        return output.getvalue()

    @classmethod
    def export_json(cls, batch_id: str) -> list[dict]:
        store = BatchStore.get_instance()
        batch = store.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        results = []
        for f in batch.files:
            if f.prediction:
                results.append(
                    {
                        "name": f.filename,
                        "result_json": f.prediction.model_dump(mode="json"),
                    }
                )
            else:
                results.append(
                    {
                        "name": f.filename,
                        "status": f.status,
                        "error_message": f.error_message or "Unknown error",
                    }
                )
        return results
