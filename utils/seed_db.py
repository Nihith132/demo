from __future__ import annotations

from database import Base, SessionLocal, engine
from models.db_models import Doctor
from utils.security import hash_password


def seed_doctors() -> None:
    Base.metadata.create_all(bind=engine)

    # MVP credentials (change in real deployments)
    seed = [
        Doctor(
            id=1,
            name="Dr. Priya Sharma",
            department="Cardiology",
            current_load=2,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            id=2,
            name="Dr. Arjun Mehta",
            department="Emergency",
            current_load=5,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            id=3,
            name="Dr. Leila Hassan",
            department="Neurology",
            current_load=1,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            id=4,
            name="Dr. James Okonkwo",
            department="General Practice",
            current_load=3,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            id=5,
            name="Dr. Sofia Reyes",
            department="Pulmonology",
            current_load=0,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            id=6,
            name="Dr. Wei Zhang",
            department="Emergency",
            current_load=4,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            id=7,
            name="Dr. Ananya Iyer",
            department="Orthopedics",
            current_load=2,
            is_available=True,
            password_hash=hash_password("password123"),
        ),
        Doctor(
            id=8,
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
            exists = db.query(Doctor).filter(Doctor.id == doctor.id).first()
            if exists:
                # Backfill auth fields if missing
                if not exists.password_hash:
                    exists.password_hash = doctor.password_hash
                continue
            db.add(doctor)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_doctors()
    print("Seed complete.")
