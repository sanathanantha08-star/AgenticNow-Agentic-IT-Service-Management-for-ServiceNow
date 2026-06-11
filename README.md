# AgenticNow: Agentic IT Service Management for ServiceNow

> An autonomous multi-agent system that transforms ServiceNow from a passive ticket log into a self-healing IT operations platform — triaging, resolving, escalating, and learning from every incident with minimal human intervention.

---

## Overview

AgenticNow is an agentic AI system built on top of ServiceNow that automates the full IT ticket lifecycle — from intake to root cause analysis. It replaces the repetitive, manual middle layer of L1 IT support with a network of specialised agents that classify, deduplicate, resolve, route, monitor, and learn — while keeping humans in the loop at every consequential decision point.

The system is built around a core principle: **the agent does the work, the human makes the call.** No ticket is closed, routed, published, or changed in production without explicit human confirmation. Every HITL gate is deliberate and purposeful — not a workaround, but a design decision.

> **ServiceNow Instance Status:** A free Personal Developer Instance (PDI) is currently unavailable due to capacity constraints on developer.servicenow.com. A mock ServiceNow client (`integrations/mock_servicenow_client.py`) has been implemented as a full drop-in replacement, mirroring every method signature of the real client. Switching to a real instance requires only setting `API_ENV=production` in `.env` — no code changes needed anywhere. The system is actively waiting for a PDI to become available.

---

## Architecture

![System Architecture](./arch.png)

The system runs two concurrent paths from the moment a ticket is routed:

- **Main path** — handles the individual ticket lifecycle end to end
- **RCA path** — runs in parallel, watching for patterns across all tickets and firing the root cause analysis sub-flow when a clustering threshold is hit

---

## Features

### Manual vs Agentic

| Feature | Manual today | With AgenticNow |
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

## Phases of Development

### ✅ Phase 1 — Project Scaffold & ServiceNow Connectivity
**Status: Complete**

- Full folder structure created for all 7 agents
- `MainState` defined in `main_graph.py`
- `.env`, `requirements.txt`, `langgraph.json` configured
- `servicenow_client.py` written with full Table API coverage
- `mock_servicenow_client.py` built as a drop-in replacement — active when `API_ENV=development`
- `integrations/__init__.py` handles client switching automatically based on `API_ENV`
- `db/checkpoint.py` stubbed — returns `None` until Phase 5 (PostgreSQL checkpointer added when HITL gates require persistence)
- `config.py` centralises all environment variables via `pydantic-settings`
- Dummy `main_graph.py` compiles and runs end to end

> **Note on ServiceNow:** PDI unavailable at time of development. Mock client mirrors the full `ServiceNowClient` API surface. Set `API_ENV=production` in `.env` to switch to the real instance when available — zero code changes required.

---

### ✅ Phase 2 — Triage Agent
**Status: Complete**

- `state.py` — `TriageAgentState` with `ticket_id`, `short_description`, `description`, `ticket_type`, `priority`, `affected_service`, `config_item`, `category`, `classification_reason`, `is_known_pattern`, `pattern_name`, `classification_written`
- `tools.py` — `get_ticket`, `write_classification` tools wrapping mock/real ServiceNow client
- `nodes.py` — `fetch_ticket_node`, `classify_node`, `write_classification_node` using Cohere `command-r-plus` with structured output
- `agent.py` — 3-node linear graph: fetch → classify → write, compiled without checkpointer
- Wired into `main_graph.py` as first node; triage always flows to duplicate agent
- All 5 mock tickets classified correctly — type, priority, category, affected service, CI, known pattern detection all verified

> **LLM:** Cohere `command-r-plus` used throughout (OpenAI substituted out). Structured output via `with_structured_output(ClassificationOutput)`.

---

### ✅ Phase 3 — Duplicate Detection Agent
**Status: Complete**

- `state.py` — `DuplicateAgentState` with `ticket_id`, `short_description`, `description`, `ticket_embedding`, `candidate_tickets`, `is_duplicate`, `duplicate_of`, `similarity_score`, `duplicate_list`, `duplicate_written`
- `tools.py` — `get_ticket`, `embed_text`, `store_embeddings`, `similarity_search`, `write_duplicate_result` tools
- `nodes.py` — `fetch_ticket_node`, `store_embeddings_node`, `embed_ticket_node`, `similarity_node`, `write_result_node`
- `agent.py` — 5-node linear graph: fetch → store embeddings → embed ticket → similarity → write result
- Local embedding model `all-MiniLM-L6-v2` via `sentence-transformers` — 384 dimensions, runs fully on device
- MongoDB local instance used as vector store — embeddings stored in `ticket_embeddings` collection
- Upsert strategy ensures fresh embeddings on every run — stale embeddings deleted before comparison
- Self-match prevention — incoming ticket excluded from MongoDB store and similarity search via two-layer guard
- Streaming enabled via `graph.stream()` — real-time node-by-node output during execution
- Wired into `main_graph.py` after triage — duplicate tickets end flow, unique tickets proceed
- Verified: TICK005 correctly flagged as duplicate of TICK001 (score 0.88), TICK002 and TICK003 correctly identified as unique

> **Threshold:** `0.8` cosine similarity. Mock data updated — TICK005 description aligned to TICK001 to simulate real duplicate submission.

---

### 🔲 Phase 4 — Context Package Agent
**Status: Not started**

- `state.py` — `ticket_id`, `classification`, `priority`, `similar_tickets`, `kb_match`, `sla_window`, `routing_suggestion`, `context_package`
- `tools.py` — `similar_tickets_search` tool, `kb_search` tool, `sla_calculator` tool
- `nodes.py` — `fetch_classification_node`, `similar_tickets_node`, `kb_search_node`, `assemble_package_node`, `write_package_node`
- `agent.py` — 5-node linear graph
- Wire into main graph after duplicate check on the "no duplicate" branch

---

### 🔲 Phase 5 — Router Agent + HITL Gate 2
**Status: Not started**

- `state.py` — `ticket_id`, `context_package`, `assigned_team`, `routing_reasoning`, `hitl_status`
- `tools.py` — `get_assignment_groups` tool, `assign_ticket` tool
- `nodes.py` — `routing_decision_node`, `hitl_gate_node` (uses `interrupt()`), `apply_routing_node`, `re_triage_node`
- `agent.py` — graph with interrupt at `hitl_gate_node`
- Wire into main graph after context package
- PostgreSQL checkpointer activated in `db/checkpoint.py` at this phase

---

### 🔲 Phase 6 — Resolver Agent + HITL Gate 1
**Status: Not started**

- `state.py` — `ticket_id`, `is_known_pattern`, `resolution_steps`, `verification_status`, `close_suggestion`
- `tools.py` — `kb_pattern_match` tool, `mock_execute_fix` tool, `mock_verify_fix` tool, `set_pending_closure` tool
- `nodes.py` — `pattern_check_node`, `execute_fix_node`, `verify_fix_node`, `suggest_close_node`, `hitl_close_confirm_node` (interrupt)
- `agent.py` — graph with fork: pattern found → execute → verify → HITL, no pattern → exit to main path

---

### 🔲 Phase 7 — Resolution Notes Agent + HITL Gate 3
**Status: Not started**

- `state.py` — `ticket_id`, `work_notes_thread`, `resolution_summary`, `notes_approved`
- `tools.py` — `get_work_notes` tool, `write_resolution_notes` tool
- `nodes.py` — `fetch_notes_node`, `draft_summary_node`, `hitl_approval_node` (interrupt), `write_notes_node`
- `agent.py` — 4-node graph with one interrupt
- Shared agent — invoked from both resolver path and main path on Resolved state change

---

### 🔲 Phase 8 — RCA Agent + HITL Gate 4
**Status: Not started**

- `state.py` — `ticket_id`, `ticket_cluster`, `problem_record_id`, `rca_hypotheses`, `confirmed_root_cause`, `workaround`, `linked_incident_ids`
- `tools.py` — `cluster_scan` tool, `create_problem_record` tool, `get_linked_incidents` tool, `get_change_history` tool, `push_workaround` tool
- `nodes.py` — `cluster_scan_node`, `threshold_check_node`, `create_problem_record_node`, `generate_hypotheses_node`, `hitl_rca_confirm_node` (interrupt), `push_workaround_node`
- `agent.py` — graph with interrupt at RCA confirmation
- Wired as parallel branch using LangGraph `Send` API

---

### 🔲 Phase 9 — Main Graph Assembly & End-to-End Test
**Status: Not started**

- Complete `main_graph.py` wiring all 7 agents as subgraphs
- Add all conditional edges and routing logic
- Add parallel RCA branch using LangGraph `Send`
- Full end-to-end test across all three paths:
  - **Main path:** ticket → triage → dedup → context package → router HITL → specialist resolves → resolution notes HITL → done
  - **Known pattern path:** password reset ticket → resolver → HITL close confirm → resolution notes → done
  - **RCA path:** 5 similar tickets → clustering fires → RCA HITL → workaround pushed → done

---

## Changelog

### v0.3.0 — 2026-06-11
**Phase 3 complete — Duplicate Detection Agent**

- Implemented `DuplicateAgentState` TypedDict with full embedding and similarity schema
- Built 5 LangChain tools: `get_ticket`, `embed_text`, `store_embeddings`, `similarity_search`, `write_duplicate_result`
- Implemented 5 nodes: `fetch_ticket_node`, `store_embeddings_node`, `embed_ticket_node`, `similarity_node`, `write_result_node`
- Integrated `all-MiniLM-L6-v2` via `sentence-transformers` as local embedding model — no API cost, 384 dimensions
- Set up local MongoDB as vector store — embeddings stored and queried from `ticket_embeddings` collection via `pymongo`
- Implemented upsert strategy in `store_embeddings` — fresh embeddings on every run, no stale data
- Fixed self-match bug — two-layer guard: incoming ticket deleted from MongoDB in `store_embeddings` and skipped in `similarity_search` loop
- Added `current_ticket_id` parameter to `similarity_search` as second safety net against self-matching
- Enabled LangGraph streaming via `graph.stream(stream_mode="updates")` — real-time node completion events with state diffs
- Updated mock data — TICK005 description aligned to TICK001 for realistic duplicate submission scenario
- Wired duplicate agent into `main_graph.py` after triage — conditional edge: duplicate → END, unique → context package (pending Phase 4)
- Verified all test cases: TICK005 flagged as duplicate of TICK001 (score 0.88), TICK002 and TICK003 correctly unique
- Updated `tests/test_triage.py` and added `tests/test_duplicate.py` with streaming output and `sys.path` fix for `tests/` subdirectory

### v0.2.0 — 2026-06-09
**Phase 2 complete — Triage Agent**

- Implemented `TriageAgentState` TypedDict with full classification schema
- Built `get_ticket` and `write_classification` LangChain tools wrapping ServiceNow client
- Implemented `fetch_ticket_node`, `classify_node`, `write_classification_node` using Cohere `command-r-plus` with structured output via `with_structured_output`
- Replaced OpenAI with Cohere throughout — removed `langchain-openai` and `openai` from requirements, added `langchain-cohere`
- Fixed priority normalisation — strips `P` prefix if LLM returns `P2` instead of `2`
- Fixed category normalisation — maps non-standard values (e.g. `connectivity`) to allowed enum
- Resolved `KeyError` on state merge — node return dicts now use exact `TriageAgentState` field names
- Resolved `ValidationError` on tool invocation — `write_classification` tool parameters aligned to state field names
- All 5 mock tickets verified: correct type, priority, category, service, CI, known pattern detection
- `main_graph.py` wired with triage as first node, flows to END pending Phase 3

### v0.1.0 — 2026-06-09
**Phase 1 complete — Project Scaffold**

- Initialised project structure for all 7 agents
- Configured `.env`, `requirements.txt`, `langgraph.json`, `config.py`
- Implemented `ServiceNowClient` with full Table API coverage (incidents, problems, KB, assignment groups)
- Implemented `MockServiceNowClient` as drop-in replacement with 5 realistic test tickets and resolved ticket history
- `integrations/__init__.py` auto-switches between mock and real client via `API_ENV` env var
- `db/checkpoint.py` stubbed — activates PostgreSQL checkpointer in Phase 5
- `main_graph.py` scaffolded with `MainState` and commented phase-by-phase build plan

---

## Project Structure

```
agenticnow/
├── arch.png
├── README.md
├── .env
├── requirements.txt
├── langgraph.json
├── config.py
├── my_agent/
│   ├── __init__.py
│   ├── main_graph.py
│   ├── triage_agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── tools.py
│   ├── duplicate_agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── tools.py
│   ├── context_package_agent/
│   │   └── __init__.py
│   ├── router_agent/
│   │   └── __init__.py
│   ├── resolver_agent/
│   │   └── __init__.py
│   ├── resolution_notes_agent/
│   │   └── __init__.py
│   └── rca_agent/
│       └── __init__.py
├── integrations/
│   ├── __init__.py
│   ├── servicenow_client.py
│   └── mock_servicenow_client.py
├── db/
│   └── checkpoint.py
└── tests/
    ├── test_triage.py
    └── test_duplicate.py
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph (StateGraph, multi-agent subgraphs) |
| LLM | Cohere `command-r-plus` (via `langchain-cohere`) |
| Embeddings | `all-MiniLM-L6-v2` via `sentence-transformers` (local, no API cost) |
| Vector store | MongoDB local (via `pymongo`) — `ticket_embeddings` collection |
| Platform | ServiceNow PDI (pending availability) / Mock client (active) |
| Backend | FastAPI (wired in Phase 9) |
| Memory & state | LangGraph checkpointer (PostgreSQL — activated Phase 5) |
| Notifications | ServiceNow webhooks + email |
| External integrations | Active Directory / Okta APIs (mocked for demo) |