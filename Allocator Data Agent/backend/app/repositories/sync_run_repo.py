from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.sync_run import SyncRun


class SyncRunRepository:
    @staticmethod
    def start(db: Session, resource: str, triggered_by_user_id: int | None) -> SyncRun:
        run = SyncRun(resource=resource, status="running", triggered_by_user_id=triggered_by_user_id)
        db.add(run)
        db.flush()
        return run

    @staticmethod
    def latest(db: Session) -> SyncRun | None:
        return db.query(SyncRun).order_by(SyncRun.started_at.desc()).first()

    @staticmethod
    def any_in_progress(db: Session) -> bool:
        return db.query(SyncRun).filter_by(status="running").first() is not None

    @staticmethod
    def latest_success_finished_at(db: Session):
        run = (
            db.query(SyncRun)
            .filter_by(status="success")
            .order_by(SyncRun.finished_at.desc())
            .first()
        )
        return run.finished_at if run else None
