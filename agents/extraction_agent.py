from __future__ import annotations

import json

from models.schemas import TriageState
from utils.groq_client import call_groq


def node_extract_symptoms(state: TriageState) -> TriageState:
    """Extraction Agent: extract structured symptoms JSON from raw input."""

    if state.get("error"):
        return state

    system_prompt = (
        "You are a clinical intake extraction assistant. "
        "Extract structured symptom information from patient-provided text. "
        "Respond ONLY with valid JSON. Do not include any preamble, explanation, or markdown code blocks."
    )

    user_prompt = (
        "Extract and return JSON with keys: "
        "chief_complaint (string), symptom_list (array of strings), duration (string), "
        "severity_indicators (array of strings), history_flags (array of strings).\n\n"
        f"RAW_INPUT:\n{state.get('raw_input','')}"
    )

    raw = call_groq(system_prompt=system_prompt, user_prompt=user_prompt)

    try:
        structured = json.loads(raw)
    except Exception as e:
        state["error"] = f"Extraction JSON parse failed: {e}"
        return state

    state["structured_symptoms"] = structured
    return state
