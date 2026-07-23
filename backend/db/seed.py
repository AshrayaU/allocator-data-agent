"""
Seed script — loads reference data that isn't user-generated.

Run via:  bin/db seed

This script must be idempotent — safe to run more than once against the same
database.  Add INSERT ... ON CONFLICT DO NOTHING statements (or equivalent
upserts) for any reference rows.

For a brand-new app this file is intentionally a no-op.  Populate it once
you have enums-as-rows, lookup tables, or an initial admin user to seed.
"""

from db.database import SessionLocal


def run() -> None:
    db = SessionLocal()
    try:
        # TODO: add idempotent seed inserts here
        db.commit()
        print("Seed complete (nothing to seed yet).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
