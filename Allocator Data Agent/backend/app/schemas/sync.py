from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SyncTriggerOut(BaseModel):
    status: str


class SyncStatusOut(BaseModel):
    last_synced_at: datetime | None
    last_sync_status: str | None
    sync_in_progress: bool
    row_counts: dict[str, int]
