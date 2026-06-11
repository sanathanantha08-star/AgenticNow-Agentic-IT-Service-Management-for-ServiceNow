# my_agent/duplicate_agent/agent.py
# ─────────────────────────────────────────────────────────────
# graph wiring only — zero logic here
# nodes, edges, compile — nothing else
# ─────────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END

from my_agent.duplicate_agent.state import DuplicateAgentState
from my_agent.duplicate_agent.nodes import (
    fetch_ticket_node,
    store_embeddings_node,
    embed_ticket_node,
    similarity_node,
    write_result_node
)


# ── build graph ────────────────────────────────────────────────
builder = StateGraph(DuplicateAgentState)

# ── register nodes ─────────────────────────────────────────────
builder.add_node("fetch",            fetch_ticket_node)
builder.add_node("store_embeddings", store_embeddings_node)
builder.add_node("embed_ticket",     embed_ticket_node)
builder.add_node("similarity",       similarity_node)
builder.add_node("write_result",     write_result_node)

# ── define edges ───────────────────────────────────────────────
builder.set_entry_point("fetch")
builder.add_edge("fetch",            "store_embeddings")
builder.add_edge("store_embeddings", "embed_ticket")
builder.add_edge("embed_ticket",     "similarity")
builder.add_edge("similarity",       "write_result")
builder.add_edge("write_result",     END)

# ── compile ────────────────────────────────────────────────────
# no checkpointer — duplicate agent has no HITL gate
graph = builder.compile()