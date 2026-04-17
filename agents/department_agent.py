from __future__ import annotations

import json
from typing import Any, Dict

from utils.groq_client import call_groq

ALLOWED_DEPARTMENTS = [
    "Cardiology",
    "Emergency",
    "Neurology",
    "General Practice",
    "Pulmonology",
    "Orthopedics",
]


def node_choose_department(state: Dict[str, Any]) -> Dict[str, Any]:
    """Choose department based on patient description (and extracted PDF text if present).

    Output:
      - state['department'] as one of ALLOWED_DEPARTMENTS

    This is used for the Patient Dashboard booking flow.
    """

    if state.get("error"):
        return state

    system_prompt = (
        "You are a medical intake router. Your job is to assign the patient to the best-fit department "
        "based ONLY on the provided text. Choose exactly one department from this list: "
        + ", ".join(ALLOWED_DEPARTMENTS)
        + ". "
        "Rules:\n"
        "- If red-flag symptoms indicating immediate life threat are present (e.g., chest pain with shortness of breath, stroke symptoms, severe allergic reaction), choose Emergency.\n"
        "- If the complaint is primarily heart/chest pain/palpitations/suspected cardiac, choose Cardiology unless it is clearly emergent in which case choose Emergency.\n"
        "- If the complaint is breathing-related (asthma flare, chronic cough, shortness of breath without emergent red flags), choose Pulmonology.\n"
        "- If the complaint is neuro-related (headache with neuro deficits, seizure history, weakness, numbness), choose Neurology unless emergent.\n"
        "- If the complaint is musculoskeletal injury, suspected fracture, joint pain, choose Orthopedics.\n"
        "- For non-urgent, general, unclear symptoms, routine follow-ups, mild infections, choose General Practice.\n"
        "Respond ONLY with valid JSON. Do not include any preamble, explanation, or markdown code blocks."
    )

    user_prompt = (
        "Return JSON with keys: department (string).\n\n"
        f"PATIENT_TEXT:\n{state.get('raw_input','')}"
    )

    raw = call_groq(system_prompt=system_prompt, user_prompt=user_prompt)

    try:
        payload = json.loads(raw)
        dept = payload.get("department")
        if dept not in ALLOWED_DEPARTMENTS:
            raise ValueError("department not in allowed list")
    except Exception as e:
        state["error"] = f"Department selection failed: {e}"
        return state

    state["department"] = dept
    return state
