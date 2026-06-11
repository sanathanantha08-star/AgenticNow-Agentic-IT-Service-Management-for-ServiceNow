# my_agent/main_graph.py

from typing import Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from db.checkpoint import get_checkpointer

from my_agent.triage_agent.agent import graph as triage_graph
from my_agent.duplicate_agent.agent import graph as duplicate_graph

# phase 4  — uncomment when context package agent is ready
# from my_agent.context_package_agent.agent import graph as context_package_graph

# phase 5  — uncomment when router agent is ready
# from my_agent.router_agent.agent import graph as router_graph

# phase 6  — uncomment when resolver agent is ready
# from my_agent.resolver_agent.agent import graph as resolver_graph

# phase 7  — uncomment when resolution notes agent is ready
# from my_agent.resolution_notes_agent.agent import graph as resolution_notes_graph

# phase 8  — uncomment when rca agent is ready
# from my_agent.rca_agent.agent import graph as rca_graph


class MainState(TypedDict):
    ticket_id:           str

    # ── triage output (phase 2) ───────────────────────────────
    is_known_pattern:    bool
    known_pattern_type:  Optional[str]
    triage_complete:     bool

    # ── duplicate output (phase 3) ────────────────────────────
    is_duplicate:        bool
    duplicate_complete:  bool

    # ── context package output (phase 4) ──────────────────────
    context_package_complete: bool

    # ── router output (phase 5) ───────────────────────────────
    hitl_status:         str
    assigned_team:       str
    router_complete:     bool

    # ── resolver output (phase 6) ─────────────────────────────
    resolver_complete:   bool

    # ── resolution notes output (phase 7) ─────────────────────
    resolution_notes_complete: bool

    # ── rca output (phase 8) ──────────────────────────────────
    rca_complete:        bool


# ── subgraph runner nodes ──────────────────────────────────────

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


def run_duplicate(state: MainState) -> dict:
    print(f"\n[Main] ── Running duplicate agent for {state['ticket_id']}")

    result = duplicate_graph.invoke({
        "ticket_id": state["ticket_id"]
    })

    print(f"[Main] ── Duplicate check complete. "
          f"is_duplicate={result['is_duplicate']}")

    return {
        "is_duplicate":      result["is_duplicate"],
        "duplicate_complete": True
    }


# phase 4 — uncomment when context package agent is ready
# def run_context_package(state: MainState) -> dict:
#     print(f"\n[Main] ── Running context package agent for {state['ticket_id']}")
#     context_package_graph.invoke({"ticket_id": state["ticket_id"]})
#     print(f"[Main] ── Context package complete.")
#     return {"context_package_complete": True}


# phase 5 — uncomment when router agent is ready
# def run_router(state: MainState) -> dict:
#     print(f"\n[Main] ── Running router agent for {state['ticket_id']}")
#     result = router_graph.invoke({"ticket_id": state["ticket_id"]})
#     print(f"[Main] ── Router complete. hitl_status={result['hitl_status']}")
#     return {
#         "hitl_status":     result["hitl_status"],
#         "assigned_team":   result["assigned_team"],
#         "router_complete": True
#     }


# phase 6 — uncomment when resolver agent is ready
# def run_resolver(state: MainState) -> dict:
#     print(f"\n[Main] ── Running resolver agent for {state['ticket_id']}")
#     result = resolver_graph.invoke({"ticket_id": state["ticket_id"]})
#     print(f"[Main] ── Resolver complete. hitl_status={result['hitl_status']}")
#     return {
#         "hitl_status":      result["hitl_status"],
#         "resolver_complete": True
#     }


# phase 7 — uncomment when resolution notes agent is ready
# def run_resolution_notes(state: MainState) -> dict:
#     print(f"\n[Main] ── Running resolution notes agent for {state['ticket_id']}")
#     resolution_notes_graph.invoke({"ticket_id": state["ticket_id"]})
#     print(f"[Main] ── Resolution notes complete.")
#     return {"resolution_notes_complete": True}


# phase 8 — uncomment when rca agent is ready
# def run_rca(state: MainState) -> dict:
#     print(f"\n[Main] ── Running RCA agent for {state['ticket_id']}")
#     rca_graph.invoke({"ticket_id": state["ticket_id"]})
#     print(f"[Main] ── RCA complete.")
#     return {"rca_complete": True}


# ── conditional edge functions ─────────────────────────────────

def route_after_duplicate(state: MainState) -> str:
    if state["is_duplicate"]:
        print(f"[Main] ── Duplicate detected — ending flow")
        return "end"
    print(f"[Main] ── Unique ticket — proceeding")
    return "context_package"


# phase 4/5 — uncomment when context package agent is ready
# def route_after_context_package(state: MainState) -> str:
#     if state["is_known_pattern"]:
#         print(f"[Main] ── Known pattern: {state['known_pattern_type']} "
#               f"— routing to resolver")
#         return "resolver"
#     print(f"[Main] ── No known pattern — routing to router")
#     return "router"


# phase 5 — uncomment when router agent is ready
# def route_after_router(state: MainState) -> str:
#     if state["hitl_status"] == "rejected":
#         print(f"[Main] ── Routing rejected — re-triaging")
#         return "triage"
#     return "rca"


# phase 6 — uncomment when resolver agent is ready
# def route_after_resolver(state: MainState) -> str:
#     if state["hitl_status"] == "approved":
#         return "resolution_notes"
#     print(f"[Main] ── Resolver fix failed — falling to context package")
#     return "context_package"


# ── graph assembly ─────────────────────────────────────────────

def build_graph():
    builder = StateGraph(MainState)

    # ── phase 2: triage ───────────────────────────────────────
    builder.add_node("triage", run_triage)
    builder.set_entry_point("triage")

    # ── phase 3: duplicate ────────────────────────────────────
    builder.add_node("duplicate", run_duplicate)
    builder.add_edge("triage", "duplicate")
    builder.add_conditional_edges(
        "duplicate",
        route_after_duplicate,
        {
            "end":             END,
            "context_package": END  # temporary — replaced in phase 4
        }
    )

    # ── phase 4: context package ──────────────────────────────
    # builder.add_node("context_package", run_context_package)
    # builder.add_conditional_edges(
    #     "context_package",
    #     route_after_context_package,
    #     {
    #         "resolver": "resolver",
    #         "router":   "router"
    #     }
    # )

    # ── phase 5: router ───────────────────────────────────────
    # builder.add_node("router", run_router)
    # builder.add_conditional_edges(
    #     "router",
    #     route_after_router,
    #     {
    #         "triage": "triage",
    #         "rca":    "rca"
    #     }
    # )

    # ── phase 6: resolver ─────────────────────────────────────
    # builder.add_node("resolver", run_resolver)
    # builder.add_conditional_edges(
    #     "resolver",
    #     route_after_resolver,
    #     {
    #         "resolution_notes": "resolution_notes",
    #         "context_package":  "context_package"
    #     }
    # )

    # ── phase 7: resolution notes ─────────────────────────────
    # builder.add_node("resolution_notes", run_resolution_notes)
    # builder.add_edge("resolution_notes", END)

    # ── phase 8: rca ──────────────────────────────────────────
    # builder.add_node("rca", run_rca)
    # builder.add_edge("rca", END)

    checkpointer = get_checkpointer()
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()