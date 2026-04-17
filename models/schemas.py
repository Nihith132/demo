from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TypedDict

from pydantic import BaseModel, Field


class PatientIntake(BaseModel):
    """Payload received at POST /api/triage/submit"""

    patient_name: str = Field(..., min_length=1, description="Full name of the patient")
    age: int = Field(..., ge=0, le=130, description="Patient age in years")
    raw_symptoms: str = Field(
        ..., description="Free-text symptom description from patient"
    )
    uploaded_file_uris: Optional[List[str]] = Field(
        default=[], description="S3/local URIs to uploaded PDF reports or images"
    )


class TriageState(TypedDict, total=False):
    """Shared state object passed between all LangGraph nodes."""

    patient_id: str
    raw_input: str
    structured_symptoms: Optional[dict]
    sbar_report: Optional[dict]
    severity_score: Optional[int]
    severity_reasoning: Optional[str]
    assigned_doctor_id: Optional[int]
    department: Optional[str]
    error: Optional[str]


class SBARReport(BaseModel):
    """Standard clinical SBAR format output from the reasoning agent."""

    situation: str = Field(
        ..., description="Concise summary of the patient's current condition"
    )
    background: str = Field(
        ..., description="Relevant medical history and context"
    )
    assessment: str = Field(
        ..., description="Clinical judgment and differential diagnosis"
    )
    recommendation: str = Field(
        ..., description="Immediate next steps and care pathway"
    )


class DoctorSchema(BaseModel):
    """Doctor record as returned by API responses."""

    id: int = Field(..., description="Doctor primary key")
    name: str = Field(..., description="Doctor name")
    department: str = Field(..., description="Department name")
    current_load: int = Field(..., description="Number of currently assigned active patients")
    is_available: bool = Field(..., description="Whether the doctor is available")


class TriageSubmitResponse(BaseModel):
    patient_id: str = Field(..., description="Tracking UUID for this triage request")
    status: str = Field(default="processing", description="Pipeline status")
    message: str = Field(..., description="Human readable status message")


class TriageStatusResponse(BaseModel):
    patient_id: str = Field(..., description="Tracking UUID for this triage request")
    status: str = Field(..., description="processing | completed | error")
    severity_score: Optional[int] = Field(default=None, description="1 (low) to 5 (critical)")
    sbar_report: Optional[SBARReport] = Field(default=None, description="SBAR report")
    assigned_doctor: Optional[DoctorSchema] = Field(
        default=None, description="Assigned doctor details"
    )


# ----------------------------
# Patient Dashboard (MVP)
# ----------------------------

class PatientIntakeUploadResponse(BaseModel):
    patient_id: str = Field(..., description="Tracking UUID for this patient intake")
    status: str = Field(..., description="processing | awaiting_booking | error")
    message: str = Field(..., description="Human readable status message")


class AvailableDoctor(DoctorSchema):
    """Doctor record shown to patients when booking."""


class PatientSelectDoctorRequest(BaseModel):
    patient_id: str = Field(..., description="Patient tracking UUID")
    doctor_id: int = Field(..., description="Doctor primary key")
    scheduled_time: datetime = Field(..., description="Requested appointment datetime (ISO 8601)")


class PatientIntakeCreateResponse(BaseModel):
    patient_id: str = Field(..., description="Patient tracking UUID")
    appointment_id: int = Field(..., description="Appointment primary key")
    status: str = Field(..., description="booked")
    message: str = Field(..., description="Human readable status message")


# ----------------------------
# Doctor Dashboard (MVP)
# ----------------------------

class SBARReportSchema(SBARReport):
    """Alias schema for embedding SBAR in dashboard entities."""


class DoctorPatientCard(BaseModel):
    patient_id: str = Field(..., description="Patient tracking UUID")
    patient_name: Optional[str] = Field(default=None, description="Patient name")
    age: Optional[int] = Field(default=None, description="Patient age")
    department: Optional[str] = Field(default=None, description="Routed department")
    scheduled_time: datetime = Field(..., description="Appointment scheduled time")
    severity_score: Optional[int] = Field(default=None, description="1-5 severity score")
    severity_reasoning: Optional[str] = Field(default=None, description="Rationale for severity score")
    ai_status: str = Field(..., description="pending | processing | ready | error")
    sbar: Optional[SBARReportSchema] = Field(default=None, description="SBAR report (doctor-only)")
    prerequisites: List[str] = Field(default_factory=list, description="Doctor-assigned prerequisites")
    ocr_required: bool = Field(default=False, description="Whether OCR is required for the uploaded PDF")


class DoctorPatientDetail(BaseModel):
    patient_id: str = Field(..., description="Patient tracking UUID")
    patient_name: Optional[str] = Field(default=None, description="Patient name")
    age: Optional[int] = Field(default=None, description="Patient age")
    department: Optional[str] = Field(default=None, description="Routed department")
    scheduled_time: datetime = Field(..., description="Appointment scheduled time")
    severity_score: Optional[int] = Field(default=None, description="1-5 severity score")
    severity_reasoning: Optional[str] = Field(default=None, description="Full reasoning behind severity")
    ai_status: str = Field(..., description="pending | processing | ready | error")
    sbar: Optional[SBARReportSchema] = Field(default=None, description="SBAR report")
    prerequisites: List[str] = Field(default_factory=list, description="Doctor-assigned prerequisites")
    ocr_required: bool = Field(default=False, description="Whether OCR is required")


class DoctorAnalyticsSummary(BaseModel):
    doctor_id: int = Field(..., description="Doctor primary key")
    total_booked: int = Field(..., description="Number of booked appointments")
    ai_ready: int = Field(..., description="Count of patients with ai_status=ready")
    ai_processing: int = Field(..., description="Count of patients with ai_status=processing")
    ai_error: int = Field(..., description="Count of patients with ai_status=error")
    ocr_required: int = Field(..., description="Count of patients flagged for OCR")
    severity_counts: dict[str, int] = Field(..., description="Counts by severity score as strings '1'..'5'")
