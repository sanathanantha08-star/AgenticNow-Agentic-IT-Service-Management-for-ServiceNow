# tests/test_duplicate.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from my_agent.duplicate_agent.agent import graph


def run_test(ticket_id: str, label: str, expected: str):
    print(f"\n{'='*55}")
    print(f"Test — {label}")
    print(f"Expected: {expected}")
    print(f"{'='*55}")

    final_state = {}

    # stream events as each node completes
    for event in graph.stream(
        {"ticket_id": ticket_id},
        stream_mode="updates"
    ):
        # event is a dict: { "node_name": { state updates from that node } }
        for node_name, updates in event.items():
            print(f"\n  ── [{node_name}] completed")

            if not updates:
                print(f"     (no state updates — side effect only)")
                continue

            for key, value in updates.items():
                # truncate long values like embeddings for readability
                if isinstance(value, list) and len(value) > 6:
                    print(f"     {key}: [{value[0]:.4f}, {value[1]:.4f}, "
                          f"... {len(value)} dims]")
                else:
                    print(f"     {key}: {value}")

        # accumulate final state
        final_state.update(list(event.values())[-1] or {})

    print(f"\n  ── Final result:")
    print(f"     is_duplicate:     {final_state.get('is_duplicate')}")
    print(f"     duplicate_of:     {final_state.get('duplicate_of')}")
    print(f"     similarity_score: {final_state.get('similarity_score')}")
    print(f"     duplicate_list:   {final_state.get('duplicate_list')}")
    print(f"     written:          {final_state.get('duplicate_written')}")


# ── run all tests ──────────────────────────────────────────────

run_test(
    ticket_id="TICK001",
    label="TICK001 — Cannot connect to VPN",
    expected="Unique — no duplicate on first run"
)

run_test(
    ticket_id="TICK005",
    label="TICK005 — VPN keeps disconnecting",
    expected="Duplicate of TICK001"
)

run_test(
    ticket_id="TICK002",
    label="TICK002 — Password reset",
    expected="Unique — different category"
)

run_test(
    ticket_id="TICK003",
    label="TICK003 — Cannot access SharePoint",
    expected="Unique — different service"
)