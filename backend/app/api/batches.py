from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse

from app.application.batch_runner import BatchProcessor
from app.config import DEFAULT_APPROACH
from app.domain.schema import BatchSummary
from app.evaluation.evaluator import ModelEvaluator
from app.security.auth import get_current_user
from app.storage.store import BatchStore

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.post("", response_model=dict)
async def create_batch(
    file: UploadFile = File(...),
    approach: Literal["approach_a", "approach_b"] = Form(DEFAULT_APPROACH),
    current_user: str = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    file_bytes = await file.read()
    try:
        batch_id, manifest_validation = BatchProcessor.process_zip_bytes(
            file_bytes, filename=file.filename, approach=approach
        )
        return {
            "batch_id": batch_id,
            "status": "processing",
            "manifest_validation": manifest_validation,
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch upload failed due to an internal processing error",
        ) from ex


@router.get("", response_model=list[BatchSummary])
def list_batches(current_user: str = Depends(get_current_user)):
    store = BatchStore.get_instance()
    return store.list_batches()


@router.get("/{batch_id}", response_model=BatchSummary)
def get_batch(batch_id: str, current_user: str = Depends(get_current_user)):
    store = BatchStore.get_instance()
    batch = store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return batch


@router.get("/{batch_id}/results.csv")
def export_csv(batch_id: str, current_user: str = Depends(get_current_user)):
    try:
        csv_content = BatchProcessor.export_csv(batch_id)
        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=call_analysis_results_{batch_id[:8]}.csv"},
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get("/{batch_id}/results.json")
def export_json(batch_id: str, current_user: str = Depends(get_current_user)):
    try:
        json_content = BatchProcessor.export_json(batch_id)
        return json_content
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get("/{batch_id}/evaluation")
def get_evaluation(batch_id: str, current_user: str = Depends(get_current_user)):
    store = BatchStore.get_instance()
    batch = store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    ground_truth = store.get_ground_truth(batch_id)
    if not ground_truth:
        return {"status": "no_ground_truth_labels", "message": "No labels.csv provided in batch upload"}

    predictions = {f.filename: f.prediction for f in batch.files if f.prediction is not None}
    metrics = ModelEvaluator.evaluate(predictions, ground_truth)
    costs = [f.metadata.estimated_cost_per_audio_minute_usd for f in batch.files if f.metadata is not None]
    metrics["estimated_cost_per_audio_minute_usd"] = round(sum(costs) / len(costs), 6) if costs else None
    return metrics
