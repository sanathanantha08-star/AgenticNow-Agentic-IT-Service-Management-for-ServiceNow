
# TicketMind — Agentic IT Service Management for ServiceNow

> An autonomous multi-agent system that transforms ServiceNow from a passive ticket log into a self-healing IT operations platform — triaging, resolving, escalating, and learning from every incident with minimal human intervention.

---

## Overview

TicketMind is a production-grade agentic AI system built on top of ServiceNow that automates the full IT ticket lifecycle — from intake to root cause analysis. It replaces the repetitive, manual middle layer of L1 IT support with a network of specialised agents that classify, deduplicate, resolve, route, monitor, and learn — while keeping humans in the loop at every consequential decision point.

The system is built around a core principle: **the agent does the work, the human makes the call.** No ticket is closed, routed, published, or changed in production without explicit human confirmation. Every HITL gate is deliberate and purposeful — not a workaround, but a design decision.

---

## Architecture

![System Architecture](./arch.png)

The system runs two concurrent paths from the moment a ticket is routed:

- **Main path** — handles the individual ticket lifecycle end to end
- **RCA path** — runs in parallel, watching for patterns across all tickets and firing the root cause analysis sub-flow when a clustering threshold is hit

---

## Features

### Manual vs Agentic

| Feature | Manual today | With TicketMind |
|---|---|---|
| Ticket classification | Agent reads and categorises manually — 4–6 min per ticket | Triage agent classifies type, priority, CI, service in under 3 seconds |
| Duplicate detection | Nobody notices 10 tickets about the same issue | Semantic similarity check on every new ticket, auto-merge on match |
| Known pattern resolution | L1 agent resolves from memory, inconsistent | Resolution Execution agent calls API, verifies fix, suggests close |
| Routing | Dispatcher guesses best team, tickets bounce | Router agent assigns to correct queue with reasoning |
| Context at handoff | Specialist receives raw ticket, rebuilds context from scratch | Full context package pre-built: KB match, similar tickets, CI, SLA window |
| SLA management | Manager checks queue manually, finds breach after it happens | SLA Watchdog monitors burn rate continuously, escalates before breach |
| User updates | User pings helpdesk for status, creates more tickets | Notification agent sends update at every state change automatically |
| Resolution documentation | Agent closes ticket without notes, knowledge lost | Resolution Notes agent drafts summary from Work Notes thread |
| KB maintenance | KB grows stale, nobody adds articles | KB Writer agent auto-publishes new articles when no match exists |
| Root cause analysis | Manual, written as a narrative, tied to nothing | Clustering agent detects patterns, RCA Hypothesis agent generates ranked causes |
| Workaround propagation | Workaround sits in Problem record, never reaches assignees | Workaround agent pushes to all linked open incidents automatically |
| Change Request creation | Raised manually or forgotten entirely | Change Request agent drafts CR with full context, CI, and proposed fix |

---

## Agents Involved

### Intake & Classification
- **Triage agent** — classifies ticket type (incident/request/problem), sets priority P1–P4, identifies affected CI and service
- **Duplicate Detection agent** — runs semantic similarity check against all open tickets; merges duplicates and notifies submitter
- **KB Search agent** — checks incoming ticket against knowledge base for a known resolvable pattern; this is the gate that decides whether a ticket ever reaches a human

### Known Pattern Branch (auto-resolve)
- **Resolution Execution agent** — calls external APIs (Active Directory, Okta, etc.) to execute the fix autonomously
- **Verification agent** — confirms fix worked via API response; on failure, routes ticket to main path as unresolved

### Main Path (escalation)
- **Context Package agent** — assembles the full context package: KB match, top 3 similar past tickets with resolutions, affected CI from CMDB, SLA window, routing recommendation with reasoning
- **Router agent** — assigns ticket to the correct specialist queue (L1/L2/L3, networking, IAM, infra) after L1 lead approval

### Parallel Background Agents
- **SLA Watchdog agent** — monitors burn rate and remaining SLA window for every open ticket; pings assignee, escalates to lead, auto-reassigns as breach approaches
- **Notification agent** — sends proactive status update to ticket submitter at every state change; eliminates inbound status pings

### Post-Resolution Agents (shared across both paths)
- **Resolution Notes agent** — triggered by ticket state changing to Resolved; drafts structured resolution summary from the full Work Notes thread
- **KB Writer agent** — checks if a KB article exists for this resolution pattern; auto-publishes a new article if none exists; no action if article already exists

### RCA Path (parallel, threshold-triggered)
- **Clustering agent** — runs on every routed ticket; detects when N semantically similar tickets sharing a CI or service cross a threshold within a time window
- **Problem Record agent** — auto-creates a Problem record in ServiceNow and links all clustered incidents to it
- **RCA Hypothesis agent** — cross-references CMDB, recent change history, and past resolutions to generate a ranked list of probable root causes with supporting evidence
- **Workaround agent** — after root cause is confirmed, pushes the workaround to the Work Notes of every linked open incident
- **Change Request agent** — drafts a Change Request with pre-filled context: affected CI, full incident history, confirmed root cause, and proposed permanent fix

**Total: 15 agents**

---

## HITL Gates

Five human checkpoints ensure no consequential action happens without sign-off:

| Gate | Trigger | Who acts | Options |
|---|---|---|---|
| **Gate 1** — Auto-resolve close | Verification agent confirms fix | L1 agent | Confirm close / reject (route to main path) |
| **Gate 2** — Routing review | Context package assembled | L1 lead | Approve / edit package / reject back to triage |
| **Gate 3** — Specialist close | Specialist finishes investigation | Specialist | Changes ticket state to Resolved |
| **Gate 4** — RCA confirmation | Hypothesis list generated | Problem coordinator | Picks confirmed root cause from ranked list |
| **Gate 5** — Change approval | CR and KB article drafted | Change Manager | Approves KB publish + CR for production pipeline |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph (StateGraph, multi-agent subgraphs) |
| LLM | GPT-4o / Claude (via API) |
| Platform | ServiceNow PDI (Personal Developer Instance) |
| Backend | FastAPI |
| Vector search | pgvector / Supabase |
| Memory & state | LangGraph checkpointer (SqliteSaver) |
| Notifications | ServiceNow webhooks + email |
| External integrations | Active Directory / Okta APIs (for resolution execution) |

---

## Project Structure

```
ticketmind/
├── architecture.png
├── README.md
├── agents/
│   ├── triage_agent.py
│   ├── duplicate_agent.py
│   ├── kb_search_agent.py
│   ├── resolution_execution_agent.py
│   ├── verification_agent.py
│   ├── context_package_agent.py
│   ├── router_agent.py
│   ├── sla_watchdog_agent.py
│   ├── notification_agent.py
│   ├── resolution_notes_agent.py
│   ├── kb_writer_agent.py
│   ├── clustering_agent.py
│   ├── problem_record_agent.py
│   ├── rca_hypothesis_agent.py
│   ├── workaround_agent.py
│   └── change_request_agent.py
├── graphs/
│   ├── main_graph.py
│   ├── known_pattern_graph.py
│   └── rca_graph.py
├── hitl/
│   └── gates.py
├── integrations/
│   ├── servicenow_client.py
│   └── okta_client.py
└── api/
    └── main.py
```