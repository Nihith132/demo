from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class PatientUser(Base):
    __tablename__ = "patient_users"

    id = Column(Integer, primary_key=True, index=True)

    # Auth (MVP)
    # Username is the patient's login identifier.
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Optional profile fields
    display_name = Column(String, nullable=True)
    email = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    records = relationship("PatientRecord", back_populates="patient_user")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)  # e.g., "Cardiology", "Emergency"
    current_load = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)

    # Auth (MVP)
    # Username is the doctor's name (login identifier).
    password_hash = Column(String, nullable=True)

    patients = relationship("PatientRecord", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")


class PatientRecord(Base):
    __tablename__ = "patient_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)  # UUID string
    patient_name = Column(String)
    age = Column(Integer)

    # Patient identity (for history)
    patient_user_id = Column(Integer, ForeignKey("patient_users.id"), nullable=True)
    patient_user = relationship("PatientUser", back_populates="records")

    # Patient dashboard input
    raw_symptoms = Column(Text)  # patient description
    uploaded_file_uris_json = Column(Text, default="[]")  # JSON string list of URIs
    pdf_extracted_text = Column(Text)
    ocr_required = Column(Boolean, default=False)

    # Department chosen by LLM (drives patient doctor list)
    department = Column(String, nullable=True)

    # Doctor dashboard outputs (populated by agents)
    structured_symptoms_json = Column(Text)  # JSON string

    sbar_situation = Column(Text)
    sbar_background = Column(Text)
    sbar_assessment = Column(Text)
    sbar_recommendation = Column(Text)

    severity_score = Column(Integer)  # 1-5
    severity_reasoning = Column(Text)  # stored explanation for score (MVP)

    ai_status = Column(String, default="pending")  # pending | processing | ready | error

    status = Column(
        String,
        default="processing",
    )  # processing | awaiting_booking | booked | completed | error

    # Assigned after patient books
    assigned_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    doctor = relationship("Doctor", back_populates="patients")

    prerequisites = Column(Text, default="[]")  # JSON array of doctor-added prerequisites

    appointments = relationship("Appointment", back_populates="patient_record")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_record_id = Column(Integer, ForeignKey("patient_records.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)

    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="booked")  # booked | completed | cancelled

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient_record = relationship("PatientRecord", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
