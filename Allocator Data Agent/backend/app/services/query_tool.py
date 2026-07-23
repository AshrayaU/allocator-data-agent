from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# The ONLY way the chat LLM touches the database. No other tool exists, and
# this one refuses anything but a single read-only SELECT — belt (regex) and
# suspenders (the connection is always rolled back, never committed, so even
# a write that somehow slipped past the regex is discarded, not persisted).
# ---------------------------------------------------------------------------

_SELECT_ONLY = re.compile(r"^\s*select\b", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|do|merge)\b",
    re.IGNORECASE,
)
_MAX_ROWS = 200


def query_data(db: Session, sql: str) -> dict:
    """Run a single read-only SELECT against the local investors/funds cache."""
    stripped = sql.strip().rstrip(";")

    if ";" in stripped:
        return {"error": "Only a single statement is allowed (no semicolons)."}
    if not _SELECT_ONLY.match(stripped):
        return {"error": "Only SELECT statements are allowed."}
    if _FORBIDDEN.search(stripped):
        return {"error": "Query contains a disallowed keyword."}

    try:
        result = db.execute(text(stripped))
        columns = list(result.keys())
        rows = result.fetchmany(_MAX_ROWS)
        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "truncated": len(rows) == _MAX_ROWS,
        }
    except Exception as exc:  # surfaced to the model as a tool error, not raised
        return {"error": str(exc)}
    finally:
        db.rollback()
