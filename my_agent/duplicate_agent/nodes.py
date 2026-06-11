from my_agent.duplicate_agent.tools import get_ticket, embed_text, store_embeddings,similarity_search,write_duplicate_result
from my_agent.duplicate_agent.state import DuplicateAgentState


#node 1 to fetch the ticket (incoming)

def fetch_ticket_node(state:DuplicateAgentState)->dict:
    print(f"Duplicate Agent: Fetching ticket {state["ticket_id"]}")
    result=get_ticket.invoke({"ticket_id": state["ticket_id"]})
    print(f"Duplicate Agent: Fetched: {result['short_description']}")
    return {
        "short_description": result["short_description"],
        "description": result["description"]
    }

#node 2: fetches all open tickets from servicenow and stores their embeddings in mongodb, excluding the incoming ticket itself
def store_embeddings_node(state: DuplicateAgentState) -> dict:
    """
    Fetches all open tickets from ServiceNow, generates embeddings
    for each one, and stores them in MongoDB.
    Excludes the incoming ticket so it is not compared against itself.
    """
    print(f"[Duplicate] Storing embeddings for all open tickets "
          f"excluding {state['ticket_id']}")

    count = store_embeddings.invoke({
        "exclude_ticket_id": state["ticket_id"]
    })

    print(f"[Duplicate] {count} tickets embedded and stored in MongoDB")

    # candidate_tickets not stored in state — they live in MongoDB
    # similarity_search reads directly from MongoDB
    return {}

#node 3: generate embedding for incoming ticket and search for similar tickets in mongodb
def embed_ticket_node(state: DuplicateAgentState)->dict:
    print(f"[Duplicate] Generating embedding for incoming ticket {state['ticket_id']}")

    text=f"{state['short_description']} {state['description']}".strip()
    if not text:
        print(f"[Duplicate] No text to embed for ticket {state['ticket_id']}")
        return {
            "ticket_embedding": []
        }
    
    embedding=embed_text.invoke({"text": text})
    print(f"[Duplicate] Generated embedding for ticket {state['ticket_id']}")
    return {
        "ticket_embedding": embedding
    }

#node 4: performs similariy search in mongodb using the incoming ticket embedding, returns list of similar tickets above threshold
def similarity_node(state: DuplicateAgentState) -> dict:
    print(f"[Duplicate] Running similarity search for "
          f"ticket {state['ticket_id']}")

    result = similarity_search.invoke({
        "ticket_embedding":  state["ticket_embedding"],
        "current_ticket_id": state["ticket_id"],
        "threshold":         0.8
    })

    print(f"[Duplicate] is_duplicate={result['is_duplicate']} "
          f"duplicate_of={result['duplicate_of']} "
          f"score={result['similarity_score']}")

    return {
        "is_duplicate":     result["is_duplicate"],
        "duplicate_of":     result["duplicate_of"],
        "similarity_score": result["similarity_score"],
        "duplicate_list":   result["duplicate_list"]
    }

def write_result_node(state: DuplicateAgentState) -> dict:
    """
    Writes duplicate detection result back to ServiceNow Work Notes.
    If duplicate: logs parent ticket and similarity score.
    If unique: logs confirmation and passes to next agent.
    """
    print(f"[Duplicate] Writing result to ServiceNow "
          f"for ticket {state['ticket_id']}")

    success = write_duplicate_result.invoke({
        "ticket_id":        state["ticket_id"],
        "is_duplicate":     state["is_duplicate"],
        "duplicate_of":     state["duplicate_of"],
        "similarity_score": state["similarity_score"],
        "duplicate_list":   state["duplicate_list"]
    })

    print(f"[Duplicate] Result written: {success}")

    return {
        "duplicate_written": success
    }