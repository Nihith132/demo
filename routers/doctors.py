from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import Appointment, Doctor, PatientRecord
from models.schemas import DoctorAnalyticsSummary, DoctorPatientCard, DoctorPatientDetail, SBARReport
from routers.auth import get_current_doctor

router = APIRouter()


class DoctorActionPayload(BaseModel):
    patient_id: str = Field(..., description="Patient tracking UUID")
    prerequisite: str = Field(..., description='e.g., "Chest X-Ray", "ECG", "CBC"')


@router.get("/dashboard", response_model=list[DoctorPatientCard])
def get_doctor_dashboard(
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Doctor dashboard (MVP): returns booked patients for this doctor as patient cards."""

    doctor_id = current_doctor.id

    rows = (
        db.query(PatientRecord, Appointment)
        .join(Appointment, Appointment.patient_record_id == PatientRecord.id)
        .filter(Appointment.doctor_id == doctor_id)
        .filter(Appointment.status == "booked")
        .order_by(PatientRecord.severity_score.desc().nullslast())
        .all()
    )

    cards: list[DoctorPatientCard] = []
    for pr, appt in rows:
        sbar = None
        if pr.sbar_situation or pr.sbar_background or pr.sbar_assessment or pr.sbar_recommendation:
            sbar = SBARReport.model_validate(
                {
                    "situation": pr.sbar_situation or "",
                    "background": pr.sbar_background or "",
                    "assessment": pr.sbar_assessment or "",
                    "recommendation": pr.sbar_recommendation or "",
                }
            )

        cards.append(
            DoctorPatientCard.model_validate(
                {
                    "patient_id": pr.patient_id,
                    "patient_name": pr.patient_name,
                    "age": pr.age,
                    "department": pr.department,
                    "scheduled_time": appt.scheduled_time,
                    "severity_score": pr.severity_score,
                    "severity_reasoning": pr.severity_reasoning,
                    "ai_status": pr.ai_status or "pending",
                    "sbar": sbar,
                    "prerequisites": json.loads(pr.prerequisites or "[]"),
                    "ocr_required": bool(pr.ocr_required),
                }
            )
        )

    return cards


@router.get("/patient/{patient_id}", response_model=DoctorPatientDetail)
def get_patient_detail(
    patient_id: str,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Doctor dashboard detail view for a specific patient card."""

    doctor_id = current_doctor.id

    pr = db.query(PatientRecord).filter(PatientRecord.patient_id == patient_id).first()
    if pr is None:
        raise HTTPException(status_code=404, detail="patient_id not found")

    if pr.assigned_doctor_id != doctor_id:
        raise HTTPException(status_code=404, detail="patient not assigned to this doctor")

    appt = (
        db.query(Appointment)
        .filter(Appointment.patient_record_id == pr.id)
        .filter(Appointment.doctor_id == doctor_id)
        .filter(Appointment.status == "booked")
        .order_by(Appointment.scheduled_time.desc())
        .first()
    )
    if appt is None:
        raise HTTPException(status_code=404, detail="appointment not found")

    sbar = None
    if pr.sbar_situation or pr.sbar_background or pr.sbar_assessment or pr.sbar_recommendation:
        sbar = SBARReport.model_validate(
            {
                "situation": pr.sbar_situation or "",
                "background": pr.sbar_background or "",
                "assessment": pr.sbar_assessment or "",
                "recommendation": pr.sbar_recommendation or "",
            }
        )

    return DoctorPatientDetail.model_validate(
        {
            "patient_id": pr.patient_id,
            "patient_name": pr.patient_name,
            "age": pr.age,
            "department": pr.department,
            "scheduled_time": appt.scheduled_time,
            "severity_score": pr.severity_score,
            "severity_reasoning": pr.severity_reasoning,
            "ai_status": pr.ai_status or "pending",
            "sbar": sbar,
            "prerequisites": json.loads(pr.prerequisites or "[]"),
            "ocr_required": bool(pr.ocr_required),
        }
    )


@router.get("/analytics", response_model=DoctorAnalyticsSummary)
def get_doctor_analytics(
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Get analytics summary for the doctor."""

    doctor_id = current_doctor.id

    rows = (
        db.query(PatientRecord)
        .join(Appointment, Appointment.patient_record_id == PatientRecord.id)
        .filter(Appointment.doctor_id == doctor_id)
        .filter(Appointment.status == "booked")
        .all()
    )

    severity_counts = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    ai_ready = ai_processing = ai_error = 0
    ocr_required = 0

    for pr in rows:
        if pr.severity_score is not None:
            key = str(pr.severity_score)
            if key in severity_counts:
                severity_counts[key] += 1

        if (pr.ai_status or "pending") == "ready":
            ai_ready += 1
        elif (pr.ai_status or "pending") == "processing":
            ai_processing += 1
        elif (pr.ai_status or "pending") == "error":
            ai_error += 1

        if pr.ocr_required:
            ocr_required += 1

    return DoctorAnalyticsSummary.model_validate(
        {
            "doctor_id": doctor_id,
            "total_booked": len(rows),
            "ai_ready": ai_ready,
            "ai_processing": ai_processing,
            "ai_error": ai_error,
            "ocr_required": ocr_required,
            "severity_counts": severity_counts,
        }
    )


@router.post("/action")
def add_prerequisite(
    payload: DoctorActionPayload,
    current_doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Add a prerequisite to the patient's record."""

    doctor_id = current_doctor.id

    rec = db.query(PatientRecord).filter(PatientRecord.patient_id == payload.patient_id).first()
    if rec is None:
        raise HTTPException(status_code=404, detail="patient_id not found")

    if rec.assigned_doctor_id != doctor_id:
        raise HTTPException(status_code=404, detail="patient not assigned to this doctor")

    existing = json.loads(rec.prerequisites or "[]")
    existing.append(payload.prerequisite)
    rec.prerequisites = json.dumps(existing)

    db.commit()
    db.refresh(rec)

    return {"status": "ok"}
