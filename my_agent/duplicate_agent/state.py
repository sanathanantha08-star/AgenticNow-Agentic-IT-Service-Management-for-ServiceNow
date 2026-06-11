from typing import Optional
from typing_extensions import TypedDict

class DuplicateAgentState(TypedDict):
    """
    The state of the duplicate detection agent.
    """
    ticket_id: str
    short_description: str
    description: str
    ticket_embedding: list[float]
    candidate_tickets: list[dict] #all open tickets from servicenow
    is_duplicate: bool
    duplicate_of: Optional[str]#parent for merging
    similarity_score: Optional[float]#highest similarity score found among candidates
    duplicate_list: list[str]
    duplicate_written: bool
