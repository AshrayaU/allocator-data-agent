"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.sync import router as sync_router
from config.settings import settings

app = FastAPI(title="allocator-qa API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes ----------------------------------------------------------------

app.include_router(chat_router)    # POST /api/chat
app.include_router(sync_router)    # POST /api/sync, GET /api/status


@app.get("/api/healthz", tags=["meta"])
def healthz() -> dict:
    """Health check — returns {"status": "ok"}."""
    return {"status": "ok"}
