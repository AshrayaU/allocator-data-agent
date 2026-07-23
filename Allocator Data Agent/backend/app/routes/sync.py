"""Sync routes — thin HTTP layer.

POST /api/sync   — kick off a background sync (click-triggered only; the
                    chat/LLM path has no way to reach this endpoint).
GET  /api/status — last sync time/status and current row counts.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.fund import Fund
from app.models.investor import Investor
from app.repositories.sync_run_repo import SyncRunRepository
from app.schemas.sync import SyncStatusOut, SyncTriggerOut
from db.database import get_db
from tasks.sync_data import run as sync_data_run

router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync", response_model=SyncTriggerOut)
def trigger_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SyncTriggerOut:
    if SyncRunRepository.any_in_progress(db):
        raise HTTPException(status_code=409, detail="A sync is already in progress.")
    # Runs sync_data_run() to completion in a worker thread (see
    # build/020_backend/026_background_tasks.md) — the response returns
    # immediately, the frontend polls /api/status for completion.
    background_tasks.add_task(asyncio.run, sync_data_run())
    return SyncTriggerOut(status="started")


@router.get("/status", response_model=SyncStatusOut)
def sync_status(
    db: Session = Depends(get_db),
) -> SyncStatusOut:
    latest = SyncRunRepository.latest(db)
    return SyncStatusOut(
        last_synced_at=SyncRunRepository.latest_success_finished_at(db),
        last_sync_status=latest.status if latest else None,
        sync_in_progress=SyncRunRepository.any_in_progress(db),
        row_counts={
            "investors": db.query(Investor).count(),
            "funds": db.query(Fund).count(),
        },
    )
