from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents.extraction_agent import node_extract_symptoms
from agents.reasoning_agent import node_generate_sbar
from models.schemas import TriageState


def build_triage_graph():
    graph = StateGraph(TriageState)

    graph.add_node("extract", node_extract_symptoms)
    graph.add_node("sbar", node_generate_sbar)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "sbar")
    graph.add_edge("sbar", END)

    return graph.compile()


triage_graph = build_triage_graph()
