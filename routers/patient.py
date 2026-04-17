from __future__ import annotations

import os
import uuid
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import Appointment, Doctor, PatientRecord
from models.schemas import (
    AvailableDoctor,
    PatientIntakeCreateResponse,
    PatientIntakeUploadResponse,
    PatientSelectDoctorRequest,
)
from routers.patient_auth import get_current_patient
from utils.pdf_extract import extract_text_from_pdf

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "utils", "patient_uploads")


def _ensure_upload_dir() -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    return UPLOAD_DIR


@router.post("/submit", response_model=PatientIntakeUploadResponse)
async def patient_submit(
    background_tasks: BackgroundTasks,
    patient_name: str = Form(...),
    age: int = Form(...),
    description: str = Form(...),
    images: Optional[List[str]] = Form(default=None),
    pdf: UploadFile = File(...),
    current_patient=Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Patient dashboard intake: description + PDF (+ optional image URIs).

    Creates PatientRecord(status='processing') and starts background processing
    to extract PDF text and choose a department.

    Requires patient JWT auth so we can store per-user history.
    """

    patient_id = str(uuid.uuid4())

    # Prefer cloud storage (Supabase Storage). Fall back to local disk if not configured.
    pdf_bytes = await pdf.read()

    uploaded_uris: list[str] = []
    local_pdf_path: str | None = None

    try:
        from utils.supabase_storage import upload_pdf_bytes

        up = upload_pdf_bytes(content=pdf_bytes, original_filename=pdf.filename or "document.pdf")
        uploaded_uris.append(f"supabase://{up.bucket}/{up.object_path}")
    except Exception:
        # Save PDF locally for MVP fallback.
        _ensure_upload_dir()
        pdf_filename = f"{patient_id}_{(pdf.filename or 'document.pdf')}".replace(os.sep, "_")
        local_pdf_path = os.path.abspath(os.path.join(UPLOAD_DIR, pdf_filename))

        async with aiofiles.open(local_pdf_path, "wb") as f:
            await f.write(pdf_bytes)

        uploaded_uris.append(local_pdf_path)

    if images:
        uploaded_uris.extend(images)

    rec = PatientRecord(
        patient_id=patient_id,
        patient_user_id=current_patient.id,
        patient_name=patient_name,
        age=age,
        raw_symptoms=description,
        uploaded_file_uris_json=str(uploaded_uris),
        status="processing",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # background processing populates department via LLM and flags OCR if needed.
    # Only run PDF text extraction when we have a local path (PyPDF expects a file path).
    if local_pdf_path:
        background_tasks.add_task(_process_patient_intake, patient_id, description, local_pdf_path)
    else:
        background_tasks.add_task(_process_patient_intake_no_pdf, patient_id, description)

    return PatientIntakeUploadResponse(
        patient_id=patient_id,
        status="processing",
        message="Patient intake received. Processing started.",
    )


def _process_patient_intake_no_pdf(patient_id: str, description: str) -> None:
    """Background: choose department based on description only (cloud PDF extraction pending)."""

    db = next(get_db())
    try:
        rec = db.query(PatientRecord).filter(PatientRecord.patient_id == patient_id).first()
        if rec is None:
            return

        from agents.department_agent import node_choose_department

        state = {
            "patient_id": patient_id,
            "raw_input": description,
            "error": None,
            "department": None,
        }

        state = node_choose_department(state)
        if state.get("error"):
            rec.status = "error"
        else:
            rec.department = state.get("department")
            rec.status = "awaiting_booking"

        db.commit()
        db.refresh(rec)
    finally:
        db.close()


def _process_patient_intake(patient_id: str, description: str, pdf_path: str) -> None:
    """Background: extract PDF text, flag OCR, choose department, persist."""

    db = next(get_db())
    try:
        rec = db.query(PatientRecord).filter(PatientRecord.patient_id == patient_id).first()
        if rec is None:
            return

        pdf_result = extract_text_from_pdf(pdf_path, max_pages=None)
        rec.pdf_extracted_text = pdf_result.extracted_text
        rec.ocr_required = pdf_result.ocr_required

        # Department selection is done by LLM based on description + extracted text.
        from agents.department_agent import node_choose_department

        state = {
            "patient_id": patient_id,
            "raw_input": description + "\n\nPDF_TEXT:\n" + (pdf_result.extracted_text or ""),
            "error": None,
            "department": None,
        }

        state = node_choose_department(state)
        if state.get("error"):
            rec.status = "error"
        else:
            rec.department = state.get("department")
            rec.status = "awaiting_booking"

        db.commit()
        db.refresh(rec)
    finally:
        db.close()


@router.get("/history")
def patient_history(
    current_patient=Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(PatientRecord)
        .filter(PatientRecord.patient_user_id == current_patient.id)
        .order_by(PatientRecord.created_at.desc())
        .all()
    )

    return [
        {
            "patient_id": r.patient_id,
            "patient_name": r.patient_name,
            "age": r.age,
            "department": r.department,
            "status": r.status,
            "ai_status": r.ai_status or "pending",
            "severity_score": r.severity_score,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/doctors", response_model=List[AvailableDoctor])
def list_available_doctors(
    patient_id: str,
    current_patient=Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    rec = (
        db.query(PatientRecord)
        .filter(PatientRecord.patient_id == patient_id)
        .filter(PatientRecord.patient_user_id == current_patient.id)
        .first()
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="patient_id not found")

    if not rec.department:
        raise HTTPException(status_code=400, detail="department not determined yet")

    doctors = (
        db.query(Doctor)
        .filter(Doctor.department == rec.department)
        .filter(Doctor.is_available == True)  # noqa: E712
        .order_by(Doctor.current_load.asc())
        .all()
    )

    return [
        AvailableDoctor.model_validate(
            {
                "id": d.id,
                "name": d.name,
                "department": d.department,
                "current_load": d.current_load,
                "is_available": d.is_available,
            }
        )
        for d in doctors
    ]


def _run_agents_after_booking(patient_id: str) -> None:
    """Background after booking: run extraction -> sbar -> severity, persist for doctor dashboard."""

    from workflow import triage_graph

    import json as _json

    db = next(get_db())
    try:
        rec = db.query(PatientRecord).filter(PatientRecord.patient_id == patient_id).first()
        if rec is None:
            return

        if rec.status != "booked":
            return

        rec.ai_status = "processing"
        db.commit()

        raw_input = (rec.raw_symptoms or "") + "\n\nPDF_TEXT:\n" + (rec.pdf_extracted_text or "")

        state = {
            "patient_id": patient_id,
            "raw_input": raw_input,
            "structured_symptoms": None,
            "sbar_report": None,
            "severity_score": None,
            "severity_reasoning": None,
            "assigned_doctor_id": rec.assigned_doctor_id,
            "error": None,
        }

        state = triage_graph.invoke(state)

        if state.get("error"):
            rec.ai_status = "error"
            rec.status = "error"
            db.commit()
            return

        if state.get("structured_symptoms") is not None:
            rec.structured_symptoms_json = _json.dumps(state["structured_symptoms"])

        if state.get("sbar_report") is not None:
            rec.sbar_situation = state["sbar_report"].get("situation")
            rec.sbar_background = state["sbar_report"].get("background")
            rec.sbar_assessment = state["sbar_report"].get("assessment")
            rec.sbar_recommendation = state["sbar_report"].get("recommendation")

        rec.severity_score = state.get("severity_score")
        rec.severity_reasoning = state.get("severity_reasoning")

        rec.ai_status = "ready"

        db.commit()
        db.refresh(rec)
    finally:
        db.close()


@router.post("/book", response_model=PatientIntakeCreateResponse)
def book_appointment(
    payload: PatientSelectDoctorRequest,
    background_tasks: BackgroundTasks,
    current_patient=Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    rec = (
        db.query(PatientRecord)
        .filter(PatientRecord.patient_id == payload.patient_id)
        .filter(PatientRecord.patient_user_id == current_patient.id)
        .first()
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="patient_id not found")

    if not rec.department:
        raise HTTPException(status_code=400, detail="department not determined yet")

    doc = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="doctor_id not found")

    if doc.department != rec.department:
        raise HTTPException(status_code=400, detail="doctor is not in the patient's department")

    if not doc.is_available:
        raise HTTPException(status_code=400, detail="doctor is not available")

    appt = Appointment(
        patient_record_id=rec.id,
        doctor_id=doc.id,
        scheduled_time=payload.scheduled_time,
        status="booked",
    )
    db.add(appt)

    # reflect assignment for doctor dashboard
    rec.assigned_doctor_id = doc.id
    rec.status = "booked"

    doc.current_load = (doc.current_load or 0) + 1

    db.commit()
    db.refresh(appt)

    # run agent pipeline AFTER booking.
    background_tasks.add_task(_run_agents_after_booking, rec.patient_id)

    return PatientIntakeCreateResponse(
        patient_id=rec.patient_id,
        appointment_id=appt.id,
        status="booked",
        message="Appointment booked.",
    )
