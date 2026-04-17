from __future__ import annotations

import re

from sqlalchemy.orm import Session

from models.db_models import Doctor
from models.schemas import TriageState


def _infer_department(severity_score: int | None, recommendation: str | None) -> str:
    if severity_score is None:
        return "General Practice"
    if severity_score >= 4:
        return "Emergency"
    if severity_score <= 2:
        return "General Practice"

    rec = (recommendation or "").lower()
    for dept in [
        "cardiology",
        "neurology",
        "pulmonology",
        "orthopedics",
        "emergency",
        "general practice",
    ]:
        if re.search(r"\b" + re.escape(dept) + r"\b", rec):
            return dept.title() if dept != "general practice" else "General Practice"

    return "General Practice"


def node_route_patient(state: TriageState, db: Session) -> TriageState:
    """Routing Manager: pick a doctor via DB lookup (no Groq call)."""

    if state.get("error"):
        return state

    dept = _infer_department(
        state.get("severity_score"),
        (state.get("sbar_report") or {}).get("recommendation"),
    )

    q = (
        db.query(Doctor)
        .filter(Doctor.is_available == True)  # noqa: E712
        .filter(Doctor.department == dept)
        .order_by(Doctor.current_load.asc())
    )
    doctor = q.first()

    if doctor is None:
        doctor = (
            db.query(Doctor)
            .filter(Doctor.is_available == True)  # noqa: E712
            .order_by(Doctor.current_load.asc())
            .first()
        )

    if doctor is None:
        state["error"] = "No available doctors."
        return state

    state["assigned_doctor_id"] = doctor.id
    return state
