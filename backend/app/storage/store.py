import json
import os
import sqlite3
import threading

from app.domain.schema import BatchSummary, CallAnalysisFileResult

from app.config import SQLITE_DB_PATH

DB_PATH = SQLITE_DB_PATH


class BatchStore:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    total_files INTEGER NOT NULL,
                    processed_files INTEGER NOT NULL,
                    failed_files INTEGER NOT NULL,
                    progress_percentage REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    files_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ground_truths (
                    batch_id TEXT PRIMARY KEY,
                    ground_truth_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

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
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO batches
                (batch_id, status, total_files, processed_files, failed_files, progress_percentage, created_at, completed_at, files_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch.batch_id,
                    batch.status,
                    batch.total_files,
                    batch.processed_files,
                    batch.failed_files,
                    batch.progress_percentage,
                    batch.created_at,
                    batch.completed_at,
                    json.dumps([]),
                ),
            )
            conn.commit()
        return batch

    def get_batch(self, batch_id: str) -> BatchSummary | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM batches WHERE batch_id = ?", (batch_id,)).fetchone()
            if not row:
                return None
            files_data = json.loads(row["files_json"])
            files = [CallAnalysisFileResult.model_validate(f) for f in files_data]
            return BatchSummary(
                batch_id=row["batch_id"],
                status=row["status"],
                total_files=row["total_files"],
                processed_files=row["processed_files"],
                failed_files=row["failed_files"],
                progress_percentage=row["progress_percentage"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
                files=files,
            )

    def list_batches(self) -> list[BatchSummary]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM batches ORDER BY created_at DESC").fetchall()
            results = []
            for row in rows:
                files_data = json.loads(row["files_json"])
                files = [CallAnalysisFileResult.model_validate(f) for f in files_data]
                results.append(
                    BatchSummary(
                        batch_id=row["batch_id"],
                        status=row["status"],
                        total_files=row["total_files"],
                        processed_files=row["processed_files"],
                        failed_files=row["failed_files"],
                        progress_percentage=row["progress_percentage"],
                        created_at=row["created_at"],
                        completed_at=row["completed_at"],
                        files=files,
                    )
                )
            return results

    def set_status(self, batch_id: str, status: str) -> None:
        with self._get_connection() as conn:
            conn.execute("UPDATE batches SET status = ? WHERE batch_id = ?", (status, batch_id))
            conn.commit()

    def update_file_result(
        self, batch_id: str, file_result: CallAnalysisFileResult, completed_at: str | None = None
    ):
        batch = self.get_batch(batch_id)
        if not batch:
            return

        existing_index = next((i for i, f in enumerate(batch.files) if f.file_id == file_result.file_id), None)
        if existing_index is not None:
            batch.files[existing_index] = file_result
        else:
            batch.files.append(file_result)

        processed_files = sum(1 for f in batch.files if f.status == "completed")
        failed_files = sum(1 for f in batch.files if f.status == "failed")
        total_done = processed_files + failed_files
        progress_percentage = round((total_done / batch.total_files) * 100.0, 1) if batch.total_files > 0 else 100.0

        status = batch.status
        if total_done >= batch.total_files:
            if failed_files > 0 and processed_files > 0:
                status = "completed_with_errors"
            elif failed_files == batch.total_files:
                status = "failed"
            else:
                status = "completed"

        files_json = json.dumps([f.model_dump() for f in batch.files])
        terminal = status in {"completed", "completed_with_errors", "failed"}
        final_completed_at = completed_at if terminal else batch.completed_at

        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE batches
                SET status = ?, processed_files = ?, failed_files = ?, progress_percentage = ?, completed_at = ?, files_json = ?
                WHERE batch_id = ?
                """,
                (
                    status,
                    processed_files,
                    failed_files,
                    progress_percentage,
                    final_completed_at,
                    files_json,
                    batch_id,
                ),
            )
            conn.commit()

    def set_ground_truth(self, batch_id: str, ground_truth: dict):
        gt_json = json.dumps({k: v.model_dump() for k, v in ground_truth.items()})
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ground_truths (batch_id, ground_truth_json) VALUES (?, ?)",
                (batch_id, gt_json),
            )
            conn.commit()

    def get_ground_truth(self, batch_id: str) -> dict | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT ground_truth_json FROM ground_truths WHERE batch_id = ?", (batch_id,)).fetchone()
            if not row:
                return None
            gt_dict = json.loads(row["ground_truth_json"])
            from app.domain.schema import PredictionResult

            return {k: PredictionResult.model_validate(v) for k, v in gt_dict.items()}
