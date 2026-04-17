from __future__ import annotations

import os

from sqlalchemy import create_engine, text


def column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).mappings().all()
    return any(r["name"] == column for r in rows)


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./triage.db")
    if not database_url.startswith("sqlite"):
        raise SystemExit("This migration helper is only intended for SQLite.")

    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    with engine.begin() as conn:
        if not column_exists(conn, "doctors", "username"):
            conn.execute(text("ALTER TABLE doctors ADD COLUMN username VARCHAR"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_doctors_username ON doctors (username)"))

        if not column_exists(conn, "doctors", "password_hash"):
            conn.execute(text("ALTER TABLE doctors ADD COLUMN password_hash VARCHAR"))

    print("SQLite migration complete.")


if __name__ == "__main__":
    main()
