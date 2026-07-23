from __future__ import annotations

from app.services import data_sync
from db.database import SessionLocal


async def run() -> None:
    """Sync investors and funds from the Allocator Admin API into the local cache.

    Click-triggered only (see app/routes/sync.py) — there is deliberately no
    scheduled/interval task file for this. Callable directly via
    `bin/task sync_data` too.
    """
    db = SessionLocal()
    try:
        data_sync.sync_all(db)
    finally:
        db.close()
