from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Literal, TypedDict

from app.config import MAX_CONCURRENT_INFERENCE
from app.domain.schema import CallAnalysisFileResult
from app.evaluation.evaluator import ModelEvaluator
from app.inference.pipeline import InferencePipeline
from app.storage.store import BatchStore

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_SIZE_BYTES = 200 * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3", ".flac", ".m4a", ".aac"}
_INFERENCE_SEMAPHORE = threading.BoundedSemaphore(MAX_CONCURRENT_INFERENCE)


class ManifestValidation(TypedDict):
    total_manifest_rows: int
    matched_files: int
    unmatched_audio_files: list[str]
    missing_audio_files: list[str]
    duplicate_manifest_rows: list[str]


class BatchProcessor:
    @classmethod
    def process_zip_bytes(
        cls,
        file_bytes: bytes,
        filename: str = "batch.zip",
        approach: Literal["approach_a", "approach_b"] = "approach_a",
    ) -> tuple[str, ManifestValidation | None]:
        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"Upload size exceeds maximum allowed limit ({MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB)")

        batch_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
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
                    normalized = member.filename.replace("\\", "/")
                    if not clean_name or clean_name.startswith(".") or normalized.startswith("/") or ".." in normalized.split("/"):
                        raise ValueError("Archive contains an unsafe path")

                    total_uncompressed_bytes += member.file_size
                    if total_uncompressed_bytes > MAX_UNCOMPRESSED_SIZE_BYTES:
                        raise ValueError("Extracted batch size exceeds maximum safety limit")

                    member_ext = os.path.splitext(clean_name)[1].lower()

                    if clean_name.lower() == "labels.csv" or member_ext == ".csv":
                        manifest_content = zf.read(member).decode("utf-8", errors="ignore")
                    elif member_ext in ALLOWED_AUDIO_EXTENSIONS:
                        if clean_name in audio_files:
                            raise ValueError(f"Archive contains duplicate audio filename '{clean_name}'")
                        audio_files[clean_name] = zf.read(member)
        elif ext in ALLOWED_AUDIO_EXTENSIONS:
            clean_name = os.path.basename(filename)
            audio_files[clean_name] = file_bytes
        elif ext == ".csv":
            raise ValueError(
                "labels.csv is a manifest, not an audio batch. Upload it together with audio files/folder, "
                "or include it inside a ZIP archive."
            )
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. Please upload audio clips (.ogg, .wav, .mp3) or a .zip archive."
            )

        if not audio_files:
            raise ValueError("No supported audio files found in upload")

        manifest_validation = None
        ground_truth = None
        if manifest_content:
            ground_truth = ModelEvaluator.parse_manifest(manifest_content)
            manifest_validation = cls._validate_manifest(list(audio_files.keys()), manifest_content)
            if manifest_validation["duplicate_manifest_rows"]:
                raise ValueError("labels.csv contains duplicate filenames")
        store.create_batch(batch_id, total_files=len(audio_files), created_at=created_at)
        if ground_truth is not None:
            store.set_ground_truth(batch_id, ground_truth)
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
    def _validate_manifest(
        cls, audio_filenames: list[str], manifest_content: str
    ) -> ManifestValidation:
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
        store.set_status(batch_id, "processing")

        for filename, audio_bytes in audio_files.items():
            file_id = str(uuid.uuid4())
            try:
                def run_inference():
                    with _INFERENCE_SEMAPHORE:
                        return InferencePipeline.analyze_audio(audio_bytes, filename, approach=approach)

                prediction, metadata = await asyncio.to_thread(run_inference)
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
                    error_message="Audio processing failed. See server logs for details.",
                )
            completed_at = datetime.now(timezone.utc).isoformat()
            store.update_file_result(batch_id, file_result, completed_at=completed_at)
            await asyncio.sleep(0.01)

    @classmethod
    def export_csv(cls, batch_id: str) -> str:
        store = BatchStore.get_instance()
        batch = store.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["name", "result_json", "status", "error_message"])
        writer.writeheader()
        for item in batch.files:
            writer.writerow({"name": item.filename, "result_json": json.dumps(item.prediction.model_dump(mode="json"), separators=(",", ":")) if item.prediction else "", "status": item.status, "error_message": item.error_message or ""})
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
