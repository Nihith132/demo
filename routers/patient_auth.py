from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import PatientUser
from utils.security import create_access_token, decode_access_token, hash_password, verify_password

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/patient-auth/login")


class PatientRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    display_name: str | None = None
    email: str | None = None


def get_current_patient(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> PatientUser:
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        patient_user_id = int(sub)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(PatientUser).filter(PatientUser.id == patient_user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


@router.post("/register")
def register(payload: PatientRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(PatientUser).filter(PatientUser.username == payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = PatientUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        email=payload.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer", "patient_user_id": user.id}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(PatientUser).filter(PatientUser.username == form_data.username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer", "patient_user_id": user.id}


@router.get("/me")
def me(current_patient: PatientUser = Depends(get_current_patient)):
    return {
        "id": current_patient.id,
        "username": current_patient.username,
        "display_name": current_patient.display_name,
        "email": current_patient.email,
    }


@router.post("/logout")
def logout():
    return {"status": "ok"}
