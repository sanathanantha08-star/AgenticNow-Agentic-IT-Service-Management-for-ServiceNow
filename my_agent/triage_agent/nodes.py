# my_agent/triage_agent/nodes.py

from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional

from my_agent.triage_agent.state import TriageAgentState
from my_agent.triage_agent.tools import get_ticket, write_classification
from config import settings


# ── LLM setup ─────────────────────────────────────────────────
llm = ChatCohere(
    model=settings.cohere_model,
    temperature=0
)


# ── structured output schema ───────────────────────────────────
class ClassificationOutput(BaseModel):
    ticket_type: str = Field(
        description="Type of ticket. Must be one of: incident, request, problem"
    )
    priority: str = Field(
        description=(
            "Priority level. Must be one of: 1, 2, 3, 4. "
            "1=critical/business down, 2=high/major impact, "
            "3=moderate/single user affected, 4=low/no urgency. "
            "Return only the number, no prefix."
        )
    )
    affected_service: str = Field(
        description=(
            "The IT service affected. "
            "e.g. VPN, SharePoint, Email, Laptop, Active Directory, Slack"
        )
    )
    config_item: str = Field(
        description=(
            "The specific configuration item involved. "
            "e.g. Cisco AnyConnect, SharePoint Online, Dell XPS 15, Okta"
        )
    )
    category: str = Field(
        description=(
            "Broad category. Must be one of: "
            "network, access, hardware, software, other"
        )
    )
    classification_reason: str = Field(
        description=(
            "One sentence explaining why you made this classification. "
            "Be specific — reference words from the ticket description."
        )
    )
    is_known_pattern: bool = Field(
        description=(
            "True if this ticket matches a type the system can resolve "
            "autonomously without human intervention. Known patterns are: "
            "password reset, account unlock, VPN reconnect, "
            "access request, software install."
        )
    )
    pattern_name: Optional[str] = Field(
        default=None,
        description=(
            "Only set if is_known_pattern is True. "
            "Must be one of: password_reset, account_unlock, vpn_reconnect, "
            "access_request, software_install. "
            "Set to null if is_known_pattern is False."
        )
    )


# ── classification prompt ──────────────────────────────────────
classification_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert IT service desk triage agent with 10 years of experience.

Your job is to read an IT support ticket and classify it accurately.

Guidelines:
- Read both the short description and full description carefully
- If urgency words appear (urgent, critical, blocked, down, cannot work),
  consider raising priority to P1 or P2
- If multiple users are affected, raise priority by one level
- Be specific about the config_item — name the actual tool or device
- For priority, return only the number: 1, 2, 3 or 4. No prefix like P2.
- For category, return only: network, access, hardware, software, or other
- For known patterns, only mark True if you are confident the system
  can fully resolve it without a human

Known resolvable patterns:
- password_reset   : user locked out, forgot password, needs password changed
- account_unlock   : account locked after failed attempts
- vpn_reconnect    : VPN not connecting, VPN errors, VPN dropping
- access_request   : needs access to a system, folder, or tool
- software_install : needs a software installed on their machine"""
    ),
    (
        "human",
        """Please classify this IT support ticket:

Short description: {short_description}

Full description:
{description}"""
    )
])

structured_llm = llm.with_structured_output(ClassificationOutput)


# ── node 1: fetch_ticket_node ──────────────────────────────────

def fetch_ticket_node(state: TriageAgentState) -> dict:
    print(f"[Triage] Fetching ticket {state['ticket_id']}")

    result = get_ticket.invoke({"ticket_id": state["ticket_id"]})

    print(f"[Triage] Fetched: {result['short_description']}")

    return {
        "short_description": result["short_description"],
        "description":       result["description"]
    }


# ── node 2: classify_node ──────────────────────────────────────

def classify_node(state: TriageAgentState) -> dict:
    print(f"[Triage] Classifying ticket {state['ticket_id']}")

    result: ClassificationOutput = structured_llm.invoke(
        classification_prompt.format_messages(
            short_description=state["short_description"],
            description=state["description"]
        )
    )

    # strip "P" prefix if LLM returns "P2" instead of "2"
    priority = result.priority.replace("P", "").strip()

    # normalise category — if LLM returns something outside allowed values
    category = result.category.lower()
    if category not in ["network", "access", "hardware", "software", "other"]:
        category = "other"

    print(f"[Triage] Type={result.ticket_type}  "
          f"Priority=P{priority}  "
          f"Category={category}  "
          f"KnownPattern={result.is_known_pattern}")

    # return keys must exactly match TriageAgentState field names
    return {
        "ticket_type":          result.ticket_type,
        "priority":             priority,
        "affected_service":     result.affected_service,
        "config_item":          result.config_item,
        "category":             category,
        "classification_reason": result.classification_reason,
        "is_known_pattern":     result.is_known_pattern,
        "pattern_name":         result.pattern_name,
    }


# ── node 3: write_classification_node ─────────────────────────

def write_classification_node(state: TriageAgentState) -> dict:
    print(f"[Triage] Writing classification to ServiceNow "
          f"for ticket {state['ticket_id']}")

    success = write_classification.invoke({
        "ticket_id":             state["ticket_id"],
        "ticket_type":           state["ticket_type"],
        "priority":              state["priority"],
        "affected_service":      state["affected_service"],
        "config_item":           state["config_item"],
        "category":              state["category"],
        "classification_reason": state["classification_reason"],
        "is_known_pattern":      state["is_known_pattern"],
        "pattern_name":          state["pattern_name"] or "N/A"
    })

    print(f"[Triage] Classification written: {success}")

    return {"classification_written": success}