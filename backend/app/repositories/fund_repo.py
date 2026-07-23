from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.fund import Fund


class FundRepository:
    @staticmethod
    def upsert_many(db: Session, rows: list[dict]) -> int:
        """Insert or update rows keyed by remote_id. Flush only — the caller
        (a service) commits."""
        if not rows:
            return 0
        stmt = pg_insert(Fund).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["remote_id"],
            set_={
                "name": stmt.excluded.name,
                "status": stmt.excluded.status,
                "raw": stmt.excluded.raw,
                "synced_at": func.now(),
            },
        )
        db.execute(stmt)
        db.flush()
        return len(rows)

    @staticmethod
    def count(db: Session) -> int:
        return db.query(func.count(Fund.id)).scalar() or 0
