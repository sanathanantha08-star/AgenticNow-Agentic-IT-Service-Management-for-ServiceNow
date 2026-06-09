from langchain_core.tools import tool
from integrations import snow


@tool
def get_ticket(ticket_id: str) -> dict:
    """
    Fetches a ticket from ServiceNow by sys_id.
    Returns short_description and description fields.
    """
    result = snow.get_ticket(ticket_id)
    return {
        "short_description": result["short_description"],
        "description":       result["description"]
    }


@tool
def write_classification(
    ticket_id:               str,
    ticket_type:             str,
    priority:                str,
    affected_service:        str,
    config_item:             str,
    category:                str,
    classification_reason:   str,
    is_known_pattern:        bool,
    pattern_name:            str
) -> bool:
    """
    Writes triage classification output back to the ServiceNow ticket.
    Sets category and priority fields.
    Appends a structured work note so humans can audit the decision.
    """
    work_note = (
        f"[Triage Agent]\n"
        f"Type:             {ticket_type}\n"
        f"Priority:         P{priority}\n"
        f"Category:         {category}\n"
        f"Affected Service: {affected_service}\n"
        f"CI:               {config_item}\n"
        f"Known Pattern:    {'Yes — ' + pattern_name if is_known_pattern else 'No'}\n"
        f"Reasoning:        {classification_reason}"
    )

    snow.patch_ticket(ticket_id, {
        "category": category,
        "priority": priority,
    })

    snow.add_work_note(ticket_id, work_note)

    return True