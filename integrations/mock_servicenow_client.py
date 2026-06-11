# integrations/mock_servicenow_client.py
# drop-in replacement for ServiceNowClient during local development
# mirrors every method signature of the real client exactly
# swap by setting API_ENV=production in .env

class MockServiceNowClient:

    def get_ticket(self, ticket_id: str) -> dict:
        tickets = {
            "TICK001": {
                "sys_id": "TICK001",
                "short_description": "Cannot connect to VPN from home",
                "description": (
                    "I am unable to connect to the company VPN since this morning. "
                    "I get error code 800 when trying to authenticate. "
                    "This is blocking me from accessing all internal tools and files."
                ),
                "state": "1",
                "priority": "3",
                "category": "",
                "assignment_group": "",
                "work_notes": ""
            },
            "TICK002": {
                "sys_id": "TICK002",
                "short_description": "Password reset request",
                "description": (
                    "I have been locked out of my account after too many failed "
                    "login attempts. I need my password reset urgently as I have "
                    "a client meeting in 2 hours."
                ),
                "state": "1",
                "priority": "2",
                "category": "",
                "assignment_group": "",
                "work_notes": ""
            },
            "TICK003": {
                "sys_id": "TICK003",
                "short_description": "Cannot access SharePoint portal",
                "description": (
                    "Getting a 403 Forbidden error when trying to access the "
                    "SharePoint intranet portal. Was working fine yesterday. "
                    "Multiple colleagues are reporting the same issue."
                ),
                "state": "1",
                "priority": "2",
                "category": "",
                "assignment_group": "",
                "work_notes": ""
            },
            "TICK004": {
                "sys_id": "TICK004",
                "short_description": "Laptop screen flickering",
                "description": (
                    "My Dell laptop screen has been flickering intermittently "
                    "since the last Windows update. Happens every 5-10 minutes "
                    "and makes it very hard to work."
                ),
                "state": "1",
                "priority": "3",
                "category": "",
                "assignment_group": "",
                "work_notes": ""
            },
           "TICK005": {
    "sys_id": "TICK005",
    "short_description": "Unable to connect to VPN from home",
    "description": (
        "I cannot connect to the company VPN from my home network. "
        "Getting error code 800 when trying to authenticate. "
        "Cannot access any internal systems or files."
    ),
    "state": "1",
    "priority": "3",
    "category": "",
    "assignment_group": "",
    "work_notes": ""
},
        }
        return tickets.get(ticket_id, tickets["TICK001"])

    def get_open_tickets(self, limit: int = 100) -> list:
        return [
            {
                "sys_id": "TICK001",
                "short_description": "Cannot connect to VPN from home",
                "description": "Unable to connect to VPN, error code 800",
                "category": "network",
                "priority": "3"
            },
            {
                "sys_id": "TICK002",
                "short_description": "Password reset request",
                "description": "Locked out after too many failed login attempts",
                "category": "access",
                "priority": "2"
            },
            {
                "sys_id": "TICK003",
                "short_description": "Cannot access SharePoint portal",
                "description": "Getting 403 forbidden on SharePoint",
                "category": "access",
                "priority": "2"
            },
            {
                "sys_id": "TICK004",
                "short_description": "Laptop screen flickering",
                "description": "Screen flickering after Windows update",
                "category": "hardware",
                "priority": "3"
            },
            {
    "sys_id": "TICK005",
    "short_description": "Unable to connect to VPN from home",
    "description": "Cannot connect to VPN, error 800, no access to internal systems",
    "category": "network",
    "priority": "3"
},
        ]

    def get_resolved_tickets(self, limit: int = 200) -> list:
        return [
            {
                "sys_id": "RES001",
                "short_description": "VPN connection issue",
                "description": "User could not connect to VPN, error 800",
                "close_notes": (
                    "Cleared VPN client cache, reset config file, "
                    "reinstalled Cisco AnyConnect. Issue resolved."
                ),
                "category": "network",
                "priority": "3"
            },
            {
                "sys_id": "RES002",
                "short_description": "Account locked out",
                "description": "User locked out after failed login attempts",
                "close_notes": (
                    "Reset password via Active Directory. "
                    "Unlocked account in Okta. User confirmed access restored."
                ),
                "category": "access",
                "priority": "4"
            },
            {
                "sys_id": "RES003",
                "short_description": "SharePoint 403 error",
                "description": "Multiple users getting 403 on SharePoint",
                "close_notes": (
                    "Identified permissions misconfiguration on SharePoint group. "
                    "Re-applied correct permissions. All users confirmed access."
                ),
                "category": "access",
                "priority": "2"
            },
            {
                "sys_id": "RES004",
                "short_description": "VPN authentication timeout",
                "description": "VPN dropping every 20 minutes",
                "close_notes": (
                    "Found session timeout policy set too low (20 min). "
                    "Updated to 8 hours. User confirmed stable connection."
                ),
                "category": "network",
                "priority": "3"
            },
            {
                "sys_id": "RES005",
                "short_description": "Screen flickering Dell laptop",
                "description": "Screen flickering after Windows update",
                "close_notes": (
                    "Rolled back display driver to previous version. "
                    "Disabled automatic driver updates. Flickering stopped."
                ),
                "category": "hardware",
                "priority": "3"
            },
        ]

    def patch_ticket(self, ticket_id: str, fields: dict) -> dict:
        print(f"[MOCK SNOW] PATCH  /incident/{ticket_id}")
        for k, v in fields.items():
            print(f"           {k}: {v}")
        return {"sys_id": ticket_id, **fields}

    def add_work_note(self, ticket_id: str, note: str) -> dict:
        print(f"[MOCK SNOW] WORK NOTE  /incident/{ticket_id}")
        print(f"            {note[:120]}{'...' if len(note) > 120 else ''}")
        return {"sys_id": ticket_id, "work_notes": note}

    def set_ticket_state(self, ticket_id: str, state: int) -> dict:
        state_map = {
            1: "New",
            2: "In Progress",
            3: "On Hold",
            6: "Resolved",
            7: "Closed"
        }
        label = state_map.get(state, str(state))
        print(f"[MOCK SNOW] STATE CHANGE  /incident/{ticket_id}  →  {label}")
        return {"sys_id": ticket_id, "state": str(state)}

    def assign_ticket(self, ticket_id: str,
                      assignment_group: str,
                      assigned_to: str = None) -> dict:
        print(f"[MOCK SNOW] ASSIGN  /incident/{ticket_id}  →  {assignment_group}")
        return {
            "sys_id": ticket_id,
            "assignment_group": assignment_group,
            "assigned_to": assigned_to or ""
        }

    def get_work_notes(self, ticket_id: str) -> list:
        return [
            {
                "value": f"[Triage Agent] Ticket received and classified.",
                "sys_created_on": "2024-01-15 09:00:00"
            },
            {
                "value": "Agent investigated the issue and found root config problem.",
                "sys_created_on": "2024-01-15 09:30:00"
            },
            {
                "value": "Applied fix and verified resolution with user.",
                "sys_created_on": "2024-01-15 10:00:00"
            }
        ]

    def write_resolution_notes(self, ticket_id: str, notes: str) -> dict:
        print(f"[MOCK SNOW] RESOLUTION NOTES  /incident/{ticket_id}")
        print(f"            {notes[:200]}{'...' if len(notes) > 200 else ''}")
        return {"sys_id": ticket_id, "close_notes": notes}

    def get_assignment_groups(self) -> list:
        return [
            {
                "sys_id": "GRP001",
                "name": "Network Operations",
                "description": "VPN, firewall, DNS, connectivity issues"
            },
            {
                "sys_id": "GRP002",
                "name": "Identity & Access Management",
                "description": "Password resets, account lockouts, permissions, Okta"
            },
            {
                "sys_id": "GRP003",
                "name": "End User Computing",
                "description": "Laptops, desktops, peripherals, Windows, Mac"
            },
            {
                "sys_id": "GRP004",
                "name": "Application Support",
                "description": "SharePoint, O365, Slack, internal apps, SaaS tools"
            },
            {
                "sys_id": "GRP005",
                "name": "Infrastructure",
                "description": "Servers, storage, databases, cloud infrastructure"
            },
            {
                "sys_id": "GRP006",
                "name": "Security Operations",
                "description": "Security incidents, malware, phishing, access anomalies"
            },
        ]

    def search_kb(self, query: str, limit: int = 5) -> list:
        kb = [
            {
                "sys_id": "KB001",
                "short_description": "How to fix VPN error 800",
                "text": (
                    "1. Open Cisco AnyConnect. "
                    "2. Go to Preferences → clear cache. "
                    "3. Delete and re-enter the VPN server address. "
                    "4. Restart the AnyConnect service. "
                    "5. Reconnect using your domain credentials."
                ),
                "category": "network"
            },
            {
                "sys_id": "KB002",
                "short_description": "Self-service password reset guide",
                "text": (
                    "Go to passwordreset.company.com. "
                    "Enter your employee ID. "
                    "Verify via authenticator app or recovery email. "
                    "Set new password. Minimum 12 characters, 1 uppercase, 1 symbol."
                ),
                "category": "access"
            },
            {
                "sys_id": "KB003",
                "short_description": "SharePoint 403 error resolution",
                "text": (
                    "403 errors are usually a permissions issue. "
                    "Contact your SharePoint site owner to verify group membership. "
                    "If site-wide: raise with Application Support for group policy check."
                ),
                "category": "access"
            },
        ]
        query_lower = query.lower()
        results = [
            k for k in kb
            if any(word in k["short_description"].lower() or
                   word in k["text"].lower()
                   for word in query_lower.split())
        ]
        return results[:limit] if results else kb[:1]

    def create_kb_article(self, short_description: str,
                           text: str,
                           category: str = "general") -> dict:
        print(f"[MOCK SNOW] CREATE KB  {short_description}")
        return {
            "sys_id": "KB_NEW_001",
            "short_description": short_description,
            "category": category,
            "workflow_state": "published"
        }

    def create_problem_record(self, short_description: str,
                               description: str) -> dict:
        print(f"[MOCK SNOW] CREATE PROBLEM  {short_description}")
        return {
            "sys_id": "PRB001",
            "short_description": short_description,
            "state": "101"
        }

    def link_incident_to_problem(self, incident_id: str,
                                  problem_id: str) -> dict:
        print(f"[MOCK SNOW] LINK  {incident_id}  →  problem {problem_id}")
        return {"sys_id": incident_id, "problem_id": problem_id}

    def test_connection(self) -> bool:
        print("[MOCK SNOW] Mock client active — no real ServiceNow instance needed")
        print("[MOCK SNOW] Set API_ENV=production in .env to use the real client")
        return True


if __name__ == "__main__":
    client = MockServiceNowClient()
    client.test_connection()
    print("\n--- get_ticket TICK001 ---")
    print(client.get_ticket("TICK001")["short_description"])
    print("\n--- get_open_tickets ---")
    print(f"{len(client.get_open_tickets())} open tickets")
    print("\n--- search_kb vpn ---")
    print(client.search_kb("vpn")[0]["short_description"])
    print("\n--- add_work_note ---")
    client.add_work_note("TICK001", "[Triage Agent] Classified as incident P3")