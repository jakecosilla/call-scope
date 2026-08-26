from fastapi import APIRouter

from app.inference.pipeline import PIPELINE_VERSION

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "callscope-api",
        "pipeline_version": PIPELINE_VERSION,
    }


@router.get("/ready")
def readiness_check():
    return {
        "status": "ready",
        "dependencies": {
            "inference_engine": "online",
            "storage": "online",
        },
    }
