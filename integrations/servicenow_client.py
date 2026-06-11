# integrations/servicenow_client.py
# all ServiceNow REST API calls live here
# no agent imports from requests directly — always go through this client

import requests
from requests.auth import HTTPBasicAuth
from typing import Optional
from config import settings


class ServiceNowClient:
    """
    Thin wrapper around the ServiceNow Table API.
    Handles auth, base URL, error handling in one place.
    """

    def __init__(self):
        self.base_url = settings.sn_base_url
        self.auth     = HTTPBasicAuth(settings.sn_user, settings.sn_password)
        self.headers  = {
            "Content-Type": "application/json",
            "Accept":        "application/json"
        }

    def _get(self, table: str, sys_id: str) -> dict:
        url = f"{self.base_url}/{table}/{sys_id}"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        response.raise_for_status()
        return response.json()["result"]

    def _patch(self, table: str, sys_id: str, body: dict) -> dict:
        url = f"{self.base_url}/{table}/{sys_id}"
        response = requests.patch(
            url, auth=self.auth, headers=self.headers, json=body
        )
        response.raise_for_status()
        return response.json()["result"]

    def _post(self, table: str, body: dict) -> dict:
        url = f"{self.base_url}/{table}"
        response = requests.post(
            url, auth=self.auth, headers=self.headers, json=body
        )
        response.raise_for_status()
        return response.json()["result"]

    def _query(self, table: str, sysparm_query: str,
               fields: Optional[str] = None,
               limit: int = 50) -> list:
        url = f"{self.base_url}/{table}"
        params = {
            "sysparm_query": sysparm_query,
            "sysparm_limit":  limit
        }
        if fields:
            params["sysparm_fields"] = fields
        response = requests.get(
            url, auth=self.auth, headers=self.headers, params=params
        )
        response.raise_for_status()
        return response.json()["result"]

    # ── Ticket (Incident) operations ─────────────────────────────────────────

    def get_ticket(self, ticket_id: str) -> dict:
        """Fetch a single incident by sys_id."""
        return self._get("incident", ticket_id)

    def patch_ticket(self, ticket_id: str, fields: dict) -> dict:
        """Update fields on an incident."""
        return self._patch("incident", ticket_id, fields)

    def get_open_tickets(self, limit: int = 100) -> list:
        """Fetch all open incidents — used by duplicate detection."""
        return self._query(
            table="incident",
            sysparm_query="active=true^state!=6",
            fields="sys_id,short_description,description,category,priority",
            limit=limit
        )

    def get_resolved_tickets(self, limit: int = 200) -> list:
        """Fetch resolved incidents — used by similar ticket search."""
        return self._query(
            table="incident",
            sysparm_query="state=6",
            fields="sys_id,short_description,description,close_notes,category,priority",
            limit=limit
        )

    def add_work_note(self, ticket_id: str, note: str) -> dict:
        """Append a work note to a ticket."""
        return self._patch("incident", ticket_id, {"work_notes": note})

    def set_ticket_state(self, ticket_id: str, state: int) -> dict:
        """
        Set ticket state.
        ServiceNow states: 1=New, 2=In Progress, 3=On Hold,
                           6=Resolved, 7=Closed
        """
        return self._patch("incident", ticket_id, {"state": str(state)})

    def assign_ticket(self, ticket_id: str,
                      assignment_group: str,
                      assigned_to: Optional[str] = None) -> dict:
        """Route a ticket to an assignment group."""
        body = {"assignment_group": assignment_group}
        if assigned_to:
            body["assigned_to"] = assigned_to
        return self._patch("incident", ticket_id, body)

    def get_work_notes(self, ticket_id: str) -> list:
        """Fetch all work notes for a ticket."""
        return self._query(
            table="sys_journal_field",
            sysparm_query=(
                f"element=work_notes^name=incident^element_id={ticket_id}"
            ),
            fields="value,sys_created_on",
            limit=100
        )

    def write_resolution_notes(self, ticket_id: str, notes: str) -> dict:
        """Write final resolution notes to the close_notes field."""
        return self._patch("incident", ticket_id, {"close_notes": notes})

    # ── Problem Record operations ─────────────────────────────────────────────

    def create_problem_record(self, short_description: str,
                               description: str) -> dict:
        """Create a Problem record — used by RCA agent."""
        return self._post("problem", {
            "short_description": short_description,
            "description":       description,
            "state":             "101"
        })

    def link_incident_to_problem(self, incident_id: str,
                                  problem_id: str) -> dict:
        """Link an incident to a Problem record."""
        return self._patch("incident", incident_id, {"problem_id": problem_id})

    # ── Assignment group lookup ───────────────────────────────────────────────

    def get_assignment_groups(self) -> list:
        """Fetch all active assignment groups — used by router agent."""
        return self._query(
            table="sys_user_group",
            sysparm_query="active=true^type=itil",
            fields="sys_id,name,description",
            limit=50
        )

    # ── Knowledge Base operations ─────────────────────────────────────────────

    def search_kb(self, query: str, limit: int = 5) -> list:
        """Search KB articles by text — used by context package agent."""
        return self._query(
            table="kb_knowledge",
            sysparm_query=f"active=true^textLIKE{query}",
            fields="sys_id,short_description,text,category",
            limit=limit
        )

    def create_kb_article(self, short_description: str, text: str,
                           category: str = "general") -> dict:
        """Create a new KB article — used by resolution notes agent."""
        return self._post("kb_knowledge", {
            "short_description": short_description,
            "text":              text,
            "category":          category,
            "workflow_state":    "published"
        })

    # ── Connectivity test ─────────────────────────────────────────────────────

    def test_connection(self) -> bool:
        """Ping ServiceNow — run this in Phase 1 setup."""
        try:
            result = self._query(
                table="incident",
                sysparm_query="active=true",
                fields="sys_id",
                limit=1
            )
            print(f"[ServiceNow] Connected to {settings.sn_instance}")
            print(f"[ServiceNow] Test query returned {len(result)} record(s)")
            return True
        except Exception as e:
            print(f"[ServiceNow] Connection failed: {e}")
            return False


if __name__ == "__main__":
    client = ServiceNowClient()
    client.test_connection()