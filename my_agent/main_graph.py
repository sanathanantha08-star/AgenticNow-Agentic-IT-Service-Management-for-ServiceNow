# my_agent/main_graph.py

from typing import Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from db.checkpoint import get_checkpointer

from my_agent.triage_agent.agent import graph as triage_graph


class MainState(TypedDict):
    ticket_id:          str

    # set by triage
    is_known_pattern:   bool
    known_pattern_type: Optional[str]

    # set by duplicate agent (phase 3)
    is_duplicate:       bool

    # set by router agent (phase 5)
    hitl_status:        str

    # tracking
    triage_complete:    bool


def run_triage(state: MainState) -> dict:
    print(f"\n[Main] ── Running triage agent for {state['ticket_id']}")

    result = triage_graph.invoke({
        "ticket_id": state["ticket_id"]
    })

    print(f"[Main] ── Triage complete. "
          f"known_pattern={result['is_known_pattern']} "
          f"type={result.get('known_pattern_type')}")

    return {
        "is_known_pattern":   result["is_known_pattern"],
        "known_pattern_type": result.get("known_pattern_type"),
        "triage_complete":    True
    }


def build_graph():
    builder = StateGraph(MainState)

    builder.add_node("triage", run_triage)

    # triage always goes to duplicate — no routing decision here
    builder.set_entry_point("triage")
    builder.add_edge("triage", END)

    # phase 3 — replace END with "duplicate" when ready:
    # builder.add_node("duplicate", run_duplicate)
    # builder.add_edge("triage", "duplicate")

    # phase 4 — add context package after duplicate:
    # builder.add_node("context_package", run_context_package)
    # builder.add_conditional_edges("duplicate", route_after_duplicate, {
    #     "end":             END,
    #     "context_package": "context_package"
    # })

    # phase 5 — known pattern fork lives inside context package output:
    # builder.add_conditional_edges("context_package", route_after_context, {
    #     "resolver": "resolver",
    #     "router":   "router"
    # })

    checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()