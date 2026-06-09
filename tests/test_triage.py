from my_agent.triage_agent.agent import graph

tickets = ["TICK001", "TICK002", "TICK003", "TICK004", "TICK005"]

for ticket_id in tickets:
    print(f"\n{'='*50}")
    print(f"Testing {ticket_id}")
    print("="*50)

    result = graph.invoke({"ticket_id": ticket_id})

    print(f"\nResult:")
    print(f"  type:          {result['ticket_type']}")
    print(f"  priority:      P{result['priority']}")
    print(f"  category:      {result['category']}")
    print(f"  service:       {result['affected_service']}")
    print(f"  ci:            {result['config_item']}")           # ← was result["ci"]
    print(f"  known_pattern: {result['is_known_pattern']}")
    print(f"  pattern_type:  {result['pattern_name']}")          # ← was result["known_pattern_type"]
    print(f"  reasoning:     {result['classification_reason']}") # ← was result["classification_reasoning"]