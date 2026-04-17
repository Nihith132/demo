from __future__ import annotations

from database import Base, SessionLocal, engine
from models.db_models import Doctor
from utils.security import hash_password


"""One-shot initializer for Supabase Postgres.

- Creates tables using SQLAlchemy metadata (quick start)
- Seeds doctors with password hashes

Login identifier is Doctor.name for MVP.

This requires DATABASE_URL to point at your Supabase Postgres instance.
"""


def seed_doctors() -> None:
    seed = [
        Doctor(
            name="Dr. Priya Sharma",
            department="Cardiology",
            current_load=2,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            name="Dr. Arjun Mehta",
            department="Emergency",
            current_load=5,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            name="Dr. Leila Hassan",
            department="Neurology",
            current_load=1,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            name="Dr. James Okonkwo",
            department="General Practice",
            current_load=3,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            name="Dr. Sofia Reyes",
            department="Pulmonology",
            current_load=0,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            name="Dr. Wei Zhang",
            department="Emergency",
            current_load=4,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            name="Dr. Ananya Iyer",
            department="Orthopedics",
            current_load=2,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            name="Dr. Marcus Williams",
            department="General Practice",
            current_load=1,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
    ]

    db = SessionLocal()
    try:
        for doctor in seed:
            exists = db.query(Doctor).filter(Doctor.name == doctor.name).first()
            if exists:
                if not exists.password_hash:
                    exists.password_hash = doctor.password_hash
                continue
            db.add(doctor)
        db.commit()
    finally:
        db.close()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    seed_doctors()
    print("Supabase init complete.")


if __name__ == "__main__":
    main()
