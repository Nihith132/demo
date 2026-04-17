from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import PatientUser
from utils.firebase_auth import verify_firebase_id_token

router = APIRouter()


def get_current_patient(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> PatientUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        decoded = verify_firebase_id_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token")

    firebase_uid = decoded.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token")

    user = db.query(PatientUser).filter(PatientUser.firebase_uid == firebase_uid).first()
    if user is None:
        user = PatientUser(
            firebase_uid=firebase_uid,
            email=decoded.get("email"),
            display_name=decoded.get("name") or decoded.get("displayName"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


@router.post("/session")
def create_patient_session(current_patient: PatientUser = Depends(get_current_patient)):
    """Validates Firebase ID token and ensures a PatientUser exists."""
    return {
        "patient_user_id": current_patient.id,
        "firebase_uid": current_patient.firebase_uid,
        "email": current_patient.email,
        "display_name": current_patient.display_name,
    }


@router.get("/me")
def me(current_patient: PatientUser = Depends(get_current_patient)):
    return {
        "id": current_patient.id,
        "firebase_uid": current_patient.firebase_uid,
        "email": current_patient.email,
        "display_name": current_patient.display_name,
    }
