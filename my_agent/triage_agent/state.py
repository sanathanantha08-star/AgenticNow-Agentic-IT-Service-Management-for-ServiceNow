from typing import Optional
from typing_extensions import TypedDict

class TriageAgentState(TypedDict):
    """
    The state of the triage agent.
    """
    ticket_id:str
    short_description:str
    description:str
    category:str
    priority:str
    is_known_pattern:bool
    pattern_name: Optional[str]
    affected_service:str
    ticket_type:str
    config_item:str
    classification_reason:str
    classification_written:bool