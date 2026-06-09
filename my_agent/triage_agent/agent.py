from langgraph.graph import StateGraph, END

from my_agent.triage_agent.state import TriageAgentState
from my_agent.triage_agent.nodes import (
    fetch_ticket_node,
    classify_node,
    write_classification_node
)

builder = StateGraph(TriageAgentState)

builder.add_node("fetch",    fetch_ticket_node)
builder.add_node("classify", classify_node)
builder.add_node("write",    write_classification_node)

builder.set_entry_point("fetch")
builder.add_edge("fetch",    "classify")
builder.add_edge("classify", "write")
builder.add_edge("write",    END)

graph = builder.compile()