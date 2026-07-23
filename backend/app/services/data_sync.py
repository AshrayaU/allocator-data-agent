from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.models.sync_run import SyncRun
from app.repositories.fund_repo import FundRepository
from app.repositories.investor_repo import InvestorRepository
from app.repositories.sync_run_repo import SyncRunRepository
from app.services import allocator_admin_service as admin_api

# Hard cap on pages per resource per sync — a bug or an unexpected API change
# should never turn a manual sync into an unbounded loop against the Admin API.
_MAX_PAGES_PER_RESOURCE = 50
_PAGE_SIZE = 200


def _normalize(record: dict | str) -> dict:
    """Best-effort extraction of remote_id/name/status from a raw API record.

    The vendored OpenAPI spec under-documents the /investors item shape (it
    lists array items as plain strings), so this is deliberately defensive.
    Revisit once the discovery step has inspected real API responses.
    """
    if not isinstance(record, dict):
        return {"remote_id": str(record), "name": None, "status": None, "raw": {"value": record}}
    remote_id = str(record.get("id") or record.get("short_token") or record.get("token") or "")
    return {
        "remote_id": remote_id,
        "name": record.get("name") or record.get("company_name"),
        "status": record.get("status"),
        "raw": record,
    }


def _paginate(list_fn: Callable[..., dict], items_key: str) -> list[dict]:
    all_rows: list[dict] = []
    page = 1
    while page <= _MAX_PAGES_PER_RESOURCE:
        payload = list_fn(page=page, per_page=_PAGE_SIZE)
        data = payload.get("data", payload)
        items = data.get(items_key, [])
        if not items:
            break
        all_rows.extend(_normalize(item) for item in items)

        pagination = data.get("pagination") or {}
        total_pages = pagination.get("total_pages")
        if total_pages is not None:
            if page >= total_pages:
                break
        elif len(items) < _PAGE_SIZE:
            break
        page += 1
    return [row for row in all_rows if row["remote_id"]]


def sync_resource(db: Session, resource: str, triggered_by_user_id: int | None = None) -> SyncRun:
    run = SyncRunRepository.start(db, resource, triggered_by_user_id)
    db.commit()
    db.refresh(run)

    try:
        if resource == "investors":
            rows = _paginate(admin_api.get_investors, "investors")
            count = InvestorRepository.upsert_many(db, rows)
        elif resource == "funds":
            rows = _paginate(admin_api.get_funds, "funds")
            count = FundRepository.upsert_many(db, rows)
        else:
            raise ValueError(f"Unknown sync resource: {resource!r}")

        run.status = "success"
        run.records_upserted = count
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        run.status = "error"
        run.error = str(exc)[:2000]
        run.finished_at = datetime.now(timezone.utc)
        db.commit()

    return run


def sync_all(db: Session, triggered_by_user_id: int | None = None) -> list[SyncRun]:
    return [
        sync_resource(db, "investors", triggered_by_user_id),
        sync_resource(db, "funds", triggered_by_user_id),
    ]
