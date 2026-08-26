import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.batches import router as batches_router
from app.api.health import router as health_router

app = FastAPI(
    title="CallScope AI API",
    description="Voice Tone and Background Noise Analysis Platform for Production Call Audio",
    version="1.0.0",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
allowed_origins = list(set([frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(batches_router)
