from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import Doctor, PatientRecord
from models.schemas import DoctorSchema, PatientIntake, SBARReport, TriageStatusResponse, TriageSubmitResponse
from workflow import triage_graph

router = APIRouter()


def _run_triage_workflow(patient_id: str, payload: PatientIntake) -> None:
    """Runs the LangGraph pipeline and writes results back to DB."""

    db = next(get_db())
    try:
        record = db.query(PatientRecord).filter(PatientRecord.patient_id == patient_id).first()
        if record is None:
            return

        state = {
            "patient_id": patient_id,
            "raw_input": payload.raw_symptoms,
            "structured_symptoms": None,
            "sbar_report": None,
            "severity_score": None,
            "assigned_doctor_id": None,
            "error": None,
        }

        state = triage_graph.invoke(state)

        if state.get("structured_symptoms") is not None:
            record.structured_symptoms_json = json.dumps(state["structured_symptoms"])

        if state.get("sbar_report") is not None:
            record.sbar_situation = state["sbar_report"].get("situation")
            record.sbar_background = state["sbar_report"].get("background")
            record.sbar_assessment = state["sbar_report"].get("assessment")
            record.sbar_recommendation = state["sbar_report"].get("recommendation")

        record.severity_score = state.get("severity_score")

        # simple routing: pick lowest-load doctor in Emergency for severity 4-5 else General Practice
        if not state.get("error"):
            dept = "Emergency" if (state.get("severity_score") or 0) >= 4 else "General Practice"
            doctor = (
                db.query(Doctor)
                .filter(Doctor.is_available == True)  # noqa: E712
                .filter(Doctor.department == dept)
                .order_by(Doctor.current_load.asc())
                .first()
            )
            if doctor:
                record.assigned_doctor_id = doctor.id
                doctor.current_load = (doctor.current_load or 0) + 1

        if state.get("error"):
            record.status = "error"
        else:
            record.status = "completed"

        db.commit()
        db.refresh(record)
    finally:
        db.close()


@router.post("/submit", response_model=TriageSubmitResponse)
async def submit_triage(
    payload: PatientIntake,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    patient_id = str(uuid.uuid4())

    rec = PatientRecord(
        patient_id=patient_id,
        patient_name=payload.patient_name,
        age=payload.age,
        raw_symptoms=payload.raw_symptoms,
        structured_symptoms_json=None,
        status="processing",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    background_tasks.add_task(_run_triage_workflow, patient_id, payload)

    return TriageSubmitResponse(
        patient_id=patient_id,
        status="processing",
        message="Triage pipeline initiated.",
    )


@router.get("/status/{patient_id}", response_model=TriageStatusResponse)
def get_triage_status(patient_id: str, db: Session = Depends(get_db)):
    rec = db.query(PatientRecord).filter(PatientRecord.patient_id == patient_id).first()
    if rec is None:
        raise HTTPException(status_code=404, detail="patient_id not found")

    doctor_schema = None
    if rec.assigned_doctor_id is not None:
        doc = db.query(Doctor).filter(Doctor.id == rec.assigned_doctor_id).first()
        if doc:
            doctor_schema = DoctorSchema.model_validate(
                {
                    "id": doc.id,
                    "name": doc.name,
                    "department": doc.department,
                    "current_load": doc.current_load,
                    "is_available": doc.is_available,
                }
            )

    sbar_schema = None
    if rec.status == "completed":
        sbar_schema = SBARReport.model_validate(
            {
                "situation": rec.sbar_situation or "",
                "background": rec.sbar_background or "",
                "assessment": rec.sbar_assessment or "",
                "recommendation": rec.sbar_recommendation or "",
            }
        )

    return TriageStatusResponse(
        patient_id=rec.patient_id,
        status=rec.status,
        severity_score=rec.severity_score,
        sbar_report=sbar_schema,
        assigned_doctor=doctor_schema,
    )
