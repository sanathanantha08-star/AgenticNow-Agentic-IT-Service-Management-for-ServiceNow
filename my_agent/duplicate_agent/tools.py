# my_agent/duplicate_agent/tools.py

import numpy as np
from typing import Optional
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from langchain_core.tools import tool
from integrations import snow
from config import settings


# ── model + db singletons ──────────────────────────────────────
_model        = SentenceTransformer("all-MiniLM-L6-v2")
_mongo_client = MongoClient(settings.mongodb_uri)
_db           = _mongo_client[settings.mongodb_db]
_collection   = _db["ticket_embeddings"]


# ── tool 1: get_ticket ─────────────────────────────────────────

@tool
def get_ticket(ticket_id: str) -> dict:
    """
    Fetches the ticket details from ServiceNow given a ticket_id.
    Returns short_description and description.
    """
    result = snow.get_ticket(ticket_id)
    return {
        "short_description": result["short_description"],
        "description":       result["description"]
    }


# ── tool 2: embed_text ─────────────────────────────────────────

@tool
def embed_text(text: str) -> list:
    """
    Generates a 384-dimensional embedding vector for the given text
    using all-MiniLM-L6-v2 running locally.
    """
    embedding = _model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


# ── tool 3: store_embeddings ───────────────────────────────────

@tool
def store_embeddings(exclude_ticket_id: str) -> int:
    """
    Fetches all open tickets from ServiceNow, generates embeddings
    for each one, and stores them in MongoDB ticket_embeddings collection.
    Skips the incoming ticket itself (exclude_ticket_id).

    Also deletes the incoming ticket from MongoDB if it was stored
    in a previous run — prevents self-match during similarity search.

    Returns the number of tickets stored.
    """
    # delete incoming ticket from MongoDB if it exists from a previous run
    # this prevents the ticket from matching itself during similarity search
    deleted = _collection.delete_one({"sys_id": exclude_ticket_id})
    if deleted.deleted_count > 0:
        print(f"[Duplicate] Removed stale embedding for "
              f"{exclude_ticket_id} from MongoDB")

    open_tickets = snow.get_open_tickets()
    stored = 0

    for ticket in open_tickets:
        sys_id = ticket.get("sys_id", "")

        # skip the incoming ticket — don't store or compare against itself
        if sys_id == exclude_ticket_id:
            continue

        text = (
            f"{ticket.get('short_description', '')} "
            f"{ticket.get('description', '')}"
        ).strip()

        if not text:
            continue

        embedding = _model.encode(text, normalize_embeddings=True).tolist()

        # upsert — update if exists, insert if not
        _collection.update_one(
            {"sys_id": sys_id},
            {"$set": {
                "sys_id":            sys_id,
                "short_description": ticket.get("short_description", ""),
                "description":       ticket.get("description", ""),
                "embedding":         embedding
            }},
            upsert=True
        )
        stored += 1

    print(f"[Duplicate] Stored/updated {stored} ticket embeddings in MongoDB")
    return stored


# ── tool 4: similarity_search ──────────────────────────────────

@tool
def similarity_search(
    ticket_embedding:  list,
    current_ticket_id: str,
    threshold:         float = 0.8
) -> dict:
    """
    Compares the incoming ticket embedding against all stored embeddings
    in MongoDB using cosine similarity.
    Skips the current ticket's own embedding if present.
    Returns the best match and all matches above the threshold.
    """
    all_stored = list(_collection.find({}, {
        "sys_id":            1,
        "short_description": 1,
        "embedding":         1
    }))

    if not all_stored:
        print("[Duplicate] No stored embeddings found in MongoDB")
        return {
            "is_duplicate":     False,
            "duplicate_of":     None,
            "similarity_score": 0.0,
            "duplicate_list":   []
        }

    incoming   = np.array(ticket_embedding)
    best_match = None
    best_score = 0.0
    duplicates = []

    for stored in all_stored:
        # skip if this is the incoming ticket's own stored embedding
        # safety net in addition to the delete in store_embeddings
        if stored["sys_id"] == current_ticket_id:
            continue

        stored_embedding = np.array(stored["embedding"])

        # cosine similarity = dot product (vectors are already normalised)
        score = float(np.dot(incoming, stored_embedding))

        # track best score regardless of threshold
        if score > best_score:
            best_score = score
            best_match = stored["sys_id"]

        # only add to duplicates list if above threshold
        if score >= threshold:
            duplicates.append({
                "sys_id":            stored["sys_id"],
                "short_description": stored.get("short_description", ""),
                "score":             score
            })

    # sort by score descending — highest similarity first
    duplicates.sort(key=lambda x: x["score"], reverse=True)

    is_duplicate = len(duplicates) > 0

    print(f"[Duplicate] Best score: {round(best_score, 4)} "
          f"| Duplicates above threshold: {len(duplicates)}")

    return {
        "is_duplicate":     is_duplicate,
        "duplicate_of":     duplicates[0]["sys_id"] if is_duplicate else None,
        "similarity_score": round(best_score, 4),
        "duplicate_list":   [d["sys_id"] for d in duplicates]
    }


# ── tool 5: write_duplicate_result ────────────────────────────

@tool
def write_duplicate_result(
    ticket_id:        str,
    is_duplicate:     bool,
    duplicate_of:     Optional[str],
    similarity_score: float,
    duplicate_list:   list
) -> bool:
    """
    Writes duplicate detection result back to the ServiceNow ticket.
    If duplicate: adds work note with parent ticket link and similarity score.
    If not duplicate: adds work note confirming uniqueness check passed.
    """
    if is_duplicate:
        work_note = (
            f"[Duplicate Detection Agent]\n"
            f"Status:           DUPLICATE DETECTED\n"
            f"Parent ticket:    {duplicate_of}\n"
            f"Similarity score: {similarity_score}\n"
            f"All duplicates:   {', '.join(duplicate_list)}\n"
            f"Action:           Ticket linked to parent. "
            f"Please review and merge if confirmed."
        )
    else:
        work_note = (
            f"[Duplicate Detection Agent]\n"
            f"Status:           UNIQUE — no duplicate found\n"
            f"Best match score: {similarity_score} "
            f"(threshold: 0.80)\n"
            f"Action:           Proceeding to context package agent."
        )

    snow.add_work_note(ticket_id, work_note)
    return True