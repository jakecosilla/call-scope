import threading

from app.domain.schema import BatchSummary, CallAnalysisFileResult


class BatchStore:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._batches: dict[str, BatchSummary] = {}
        self._ground_truths: dict[str, dict] = {}

    @classmethod
    def get_instance(cls) -> "BatchStore":
        with cls._lock:
            if cls._instance is None:
                cls._instance = BatchStore()
            return cls._instance

    def create_batch(self, batch_id: str, total_files: int, created_at: str) -> BatchSummary:
        batch = BatchSummary(
            batch_id=batch_id,
            status="uploaded",
            total_files=total_files,
            processed_files=0,
            failed_files=0,
            progress_percentage=0.0,
            created_at=created_at,
            files=[],
        )
        self._batches[batch_id] = batch
        return batch

    def get_batch(self, batch_id: str) -> BatchSummary | None:
        return self._batches.get(batch_id)

    def list_batches(self) -> list[BatchSummary]:
        return list(self._batches.values())

    def update_file_result(
        self, batch_id: str, file_result: CallAnalysisFileResult, completed_at: str | None = None
    ):
        batch = self._batches.get(batch_id)
        if not batch:
            return

        existing_index = next((i for i, f in enumerate(batch.files) if f.file_id == file_result.file_id), None)
        if existing_index is not None:
            batch.files[existing_index] = file_result
        else:
            batch.files.append(file_result)

        if file_result.status == "failed":
            batch.failed_files += 1
        elif file_result.status == "completed":
            batch.processed_files += 1

        total_done = batch.processed_files + batch.failed_files
        batch.progress_percentage = round((total_done / batch.total_files) * 100.0, 1) if batch.total_files > 0 else 100.0

        if total_done >= batch.total_files:
            if batch.failed_files > 0 and batch.processed_files > 0:
                batch.status = "completed_with_errors"
            elif batch.failed_files == batch.total_files:
                batch.status = "failed"
            else:
                batch.status = "completed"
            batch.completed_at = completed_at

    def set_ground_truth(self, batch_id: str, ground_truth: dict):
        self._ground_truths[batch_id] = ground_truth

    def get_ground_truth(self, batch_id: str) -> dict | None:
        return self._ground_truths.get(batch_id)
