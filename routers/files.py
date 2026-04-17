from __future__ import annotations

import ast
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import PatientRecord
from routers.auth import get_current_doctor
from routers.patient_auth import get_current_patient
from utils.supabase_storage import create_signed_pdf_url

router = APIRouter()


def _load_uploaded_uris(raw: str | None) -> list[str]:
    if not raw:
        return []
    # stored as str(list) in MVP; use ast.literal_eval for safety.
    try:
        v = ast.literal_eval(raw)
        if isinstance(v, list):
            return [str(x) for x in v]
    except Exception:
        return []
    return []


def _parse_supabase_uri(uri: str) -> tuple[str, str] | None:
    if not uri.startswith("supabase://"):
        return None
    rest = uri[len("supabase://") :]
    if "/" not in rest:
        return None
    bucket, object_path = rest.split("/", 1)
    return bucket, object_path


@router.get("/patient/pdf/signed-url")
def get_patient_pdf_signed_url(
    patient_id: str,
    current_patient=Depends(get_current_patient),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rec = (
        db.query(PatientRecord)
        .filter(PatientRecord.patient_id == patient_id)
        .filter(PatientRecord.patient_user_id == current_patient.id)
        .first()
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="patient_id not found")

    uris = _load_uploaded_uris(rec.uploaded_file_uris_json)
    supa = next((u for u in uris if u.startswith("supabase://")), None)
    if not supa:
        raise HTTPException(status_code=404, detail="No cloud PDF found for this record")

    parsed = _parse_supabase_uri(supa)
    if not parsed:
        raise HTTPException(status_code=400, detail="Invalid stored PDF URI")

    bucket, object_path = parsed
    url = create_signed_pdf_url(bucket=bucket, object_path=object_path)

    return {"patient_id": patient_id, "signed_url": url}


@router.get("/doctor/pdf/signed-url")
def get_doctor_pdf_signed_url(
    patient_id: str,
    current_doctor=Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rec = db.query(PatientRecord).filter(PatientRecord.patient_id == patient_id).first()
    if rec is None:
        raise HTTPException(status_code=404, detail="patient_id not found")

    if rec.assigned_doctor_id != current_doctor.id:
        raise HTTPException(status_code=404, detail="patient not assigned to this doctor")

    uris = _load_uploaded_uris(rec.uploaded_file_uris_json)
    supa = next((u for u in uris if u.startswith("supabase://")), None)
    if not supa:
        raise HTTPException(status_code=404, detail="No cloud PDF found for this record")

    parsed = _parse_supabase_uri(supa)
    if not parsed:
        raise HTTPException(status_code=400, detail="Invalid stored PDF URI")

    bucket, object_path = parsed
    url = create_signed_pdf_url(bucket=bucket, object_path=object_path)

    return {"patient_id": patient_id, "signed_url": url}
