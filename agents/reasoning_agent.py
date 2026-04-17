from __future__ import annotations

import json

from models.schemas import SBARReport, TriageState
from utils.groq_client import call_groq


SEVERITY_SCALE = """Severity scale (must be used verbatim):
1=Non-Urgent: Routine checkup, prescription renewal, mild cold -> General Practice
2=Low: Mild infection, chronic condition flare, minor injury -> General Practice
3=Moderate: Persistent fever, moderate pain, controlled bleeding, suspected fracture -> Specialty (matched)
4=High: Severe abdominal pain, high fever (>39.5°C), acute allergic reaction -> Emergency
5=Critical: Chest pain, loss of consciousness, respiratory failure, stroke symptoms -> Emergency
"""


def node_generate_sbar(state: TriageState) -> TriageState:
    """Clinical Reasoning Agent: generate SBAR + severity score."""

    if state.get("error"):
        return state

    system_prompt = (
        "You are a clinical triage assistant. Use the provided severity scale to assign a severity score. "
        "Return a standard SBAR report. "
        + SEVERITY_SCALE
        + "\nAlso provide a concise rationale for the severity score as 'severity_reasoning'. "
        + "Respond ONLY with valid JSON. Do not include any preamble, explanation, or markdown code blocks."
    )

    user_prompt = (
        "Given the structured symptoms JSON below, return ONLY JSON with keys: "
        "situation, background, assessment, recommendation, severity_score (int 1-5), severity_reasoning (string).\n\n"
        f"STRUCTURED_SYMPTOMS:\n{json.dumps(state.get('structured_symptoms', {}))}"
    )

    raw = call_groq(system_prompt=system_prompt, user_prompt=user_prompt)

    try:
        payload = json.loads(raw)
    except Exception as e:
        state["error"] = f"SBAR JSON parse failed: {e}"
        return state

    try:
        severity = int(payload.get("severity_score"))
        if severity < 1 or severity > 5:
            raise ValueError("severity_score out of range")
    except Exception as e:
        state["error"] = f"Invalid severity_score: {e}"
        return state

    try:
        report = SBARReport.model_validate(
            {
                "situation": payload.get("situation"),
                "background": payload.get("background"),
                "assessment": payload.get("assessment"),
                "recommendation": payload.get("recommendation"),
            }
        )
    except Exception as e:
        state["error"] = f"SBAR validation failed: {e}"
        return state

    state["sbar_report"] = report.model_dump()
    state["severity_score"] = severity
    state["severity_reasoning"] = payload.get("severity_reasoning")
    return state
