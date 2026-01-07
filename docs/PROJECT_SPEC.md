# Project Spec (MVP) — Real-Time AI Pharmacy Agent (GPT-5 + LangGraph)

Purpose: Light PRD + Technical Design for an MVP that satisfies the home assignment requirements (streaming, stateless, Hebrew+English, tools/workflows, synthetic DB, UI, eval plan, Docker, evidence screenshots).

Assignment link: [Home Assignment PDF](HOME_ASSIGNMENT.md)

---

## 1) Product Requirements (MVP)

### 1.1 Product Summary

Build a real-time conversational AI pharmacy agent on the OpenAI API that supports workflows via tools for:

- Prescription management
- Inventory control
- Customer service

Customers ask about medications, availability, prescription requirements, and safe usage. The agent must provide factual information only and avoid medical advice or diagnosis.

### 1.2 Key Requirements (from assignment)

- Real-time text streaming agent based on GPT-5
- Agent is stateless
- Works in Hebrew and English
- At least 3 tools with clear API design
- Synthetic DB with 10 users and 5 medications
- A UI to interact with the agent
- At least three distinct multi-step
- Evaluation plan
- Dockerfile + README + 2–3 screenshots as evidence

### 1.3 MVP Scope

The MVP will deliver:

- A minimal web chat UI (single page) with streaming responses
- A stateless backend that orchestrates multi-step workflows via tools
- A seeded synthetic DB (10 users, 5 medications, sample prescriptions, inventory)
- Exactly 3 core multi-step flows, each end-to-end
- A lightweight evaluation plan + a small test set including Hebrew coverage

### 1.4 Non-Goals (MVP)

- No diagnosis, no personalized medical advice
- No purchase encouragement or upsell
- No payments, checkout, delivery scheduling
- No robust identity verification (MVP uses simple user lookup)

### 1.5 Behavior & Safety Policy (MVP)

The agent must:

- Provide factual information about medications, including:
  - dosage/usage instructions (label-style)
  - prescription requirements
  - stock availability
  - active ingredients
- Never provide medical advice/diagnosis or encourage purchase
- If the user asks for advice/diagnosis: refuse + redirect to a healthcare professional or general resources

### 1.6 Bilingual UX (Hebrew + English)

- Default behavior: respond in the same language as the user’s most recent message (Hebrew ↔ English).
- The UI may optionally include a “Language: Auto / EN / HE” toggle, but Auto is the MVP default.

### 1.7 Multi-Step Flows (MVP)

The assignment expects at least three distinct multi-step flows.
We will align them 1:1 with the objective domains (customer service, inventory, prescriptions).

Flow A — Medication Info (Customer Service)
User goal: “Tell me about X / what are the ingredients / how is it taken?”

1. Agent resolves medication by name (tool)
2. Agent returns factual fields: active ingredients, dosage/usage instructions, warnings, Rx requirement
3. If user requests advice/diagnosis → refuse + redirect

Flow B — Inventory Check (Inventory Control)
User goal: “Do you have X in stock?”

1. Resolve medication by name (tool)
2. Check inventory for default store (tool)
3. Return availability and (optionally) restock ETA
4. If medication name is ambiguous → ask clarifying question

Flow C — Prescription Status / Refill (Prescription Management)
User goal: “Can I refill? What prescriptions do I have?”

1. Ask for identifier (email/phone) if missing
2. Retrieve user prescriptions (tool)
3. If multiple prescriptions, ask which one
4. Request refill or show status (tool)
5. Return confirmation + any constraints (e.g., no refills left)

### 1.8 MVP Milestones (fast plan)

M0 — Repo + scaffolding

- Python/FastAPI skeleton, uv config, basic UI stub

M1 — Data layer

- SQLite schema + seed script (10 users, 5 meds)

M2 — Tools

- Implement 3 tools with documented schemas/errors/fallbacks

M3 — Agent orchestration + streaming

- LangGraph workflow + streaming chat endpoint

M4 — Flows + evaluation

- Demonstrate 3 flows end-to-end
- Add minimal test cases (EN + HE)

M5 — Packaging + evidence

- Dockerfile + README + 2–3 screenshots

---

## 2) Technical Design (MVP)

### 2.1 Tech Stack

- Backend: Python + FastAPI
- Agent orchestration: LangGraph (graph-based workflow for multi-step flows + tool routing)
- LLM API: OpenAI API (GPT-5)
- Streaming: HTTP streaming (SSE-style text/event-stream over a streaming response)
- Database: SQLite (synthetic seeded dataset)
- UI: Minimal single-page web chat UI (HTML + vanilla JS) served by FastAPI as static files  
  Rationale: fastest path, minimal moving parts, easy Docker story, still supports streaming.
- Dependency management: uv + pyproject.toml (no requirements.txt)
- Containerization: Dockerfile

### 2.2 Engineering Requirements (MVP)

- Stateless backend: no server-side session storage. The client sends conversation history each turn.
- Tool contracts are explicit: name/purpose, input types, output schema, error handling, fallback behavior.
- Policy adherence: enforce “facts-only”, refuse advice/diagnosis requests.
- Testing rigor: include Hebrew coverage and multiple variations per flow.
- Basic observability: structured logs for tool calls, refusals, and latency.

### 2.3 High-Level Architecture (MVP)

Browser UI (static SPA)

- stores chat history
- sends history -> POST /chat/stream
- renders streaming tokens/events

FastAPI Backend (stateless)

- LangGraph workflow per request
- OpenAI GPT-5 streaming
- tool execution (SQLite-backed tools)

SQLite (seeded synthetic DB)

- users, medications, prescriptions, inventory

### 2.4 System Design Details

A) UI Design (MVP)
Implementation: apps/web/index.html + apps/web/app.js (and optional style.css), served via FastAPI static mount.

UI features (MVP):

- Message list (user + assistant)
- Text input + send
- Streaming rendering of assistant response
- Optional “Show tool events” toggle (nice-to-have, lightweight)
- Language mode: Auto (respond in user language), optional dropdown (Auto/EN/HE)

B) API Surface (MVP)

- GET / -> serves the UI
- POST /chat/stream -> streaming response
  - Input: messages[] (conversation history), optional user_identifier, optional lang_mode
  - Output: stream of events
    - token events for assistant text
    - optional tool_call / tool_result events (dev-friendly)

C) LangGraph Orchestrator (MVP)
We implement the agent as a small LangGraph state machine to make multi-step workflows explicit and testable.

State (request-scoped only):

- messages: full history from client
- lang: detected or forced (Auto/EN/HE)
- user_id: resolved from identifier (optional)
- tool_context: transient tool outputs for response composition

Nodes (conceptual):

1. detect_language (or use lang_mode)
2. policy_guard (if advice/diagnosis requested -> refusal path)
3. route_intent (med info vs inventory vs prescription)
4. call_tool(s) (may be multiple sequential calls)
5. compose_response (facts-only, language-matched, final answer)

Statelessness note:
We do not use persistent LangGraph memory/checkpointing in the MVP; all state is request-scoped and supplied by the client.

D) Tooling Layer (Minimum 3 tools)
We will design at least 3 tools and document each with inputs/outputs/errors/fallbacks.

Tool 1 — get_medication_by_name

- Purpose: resolve medication by EN/HE name
- Output: medication_id + factual label fields (active ingredients, dosage/usage, warnings, Rx requirement)
- Errors: NOT_FOUND, AMBIGUOUS
- Fallback: ask clarifying question on ambiguity

Tool 2 — check_inventory

- Purpose: check stock for medication_id in a store
- Output: in_stock, optional qty, optional restock_eta
- Errors: NOT_FOUND, INTERNAL
- Fallback: if out of stock -> provide status + optional ETA (no purchase encouragement)

Tool 3 — prescription_management

- Purpose: user prescription workflows (list + refill/status)
- Inputs: user_identifier and/or user_id, action enum (LIST, REFILL_STATUS), optional prescription_id
- Errors: UNAUTHORIZED (user not found), NOT_FOUND (prescription not found), INVALID_STATE
- Fallback: if multiple prescriptions -> ask which one

E) Data Layer (SQLite) + Seed
We will create a synthetic DB of 10 users and 5 medications.

Tables (MVP):

- users(user_id, name, phone, email)
- medications(med_id, name_en, name_he, active_ingredients, dosage_en, dosage_he, rx_required, warnings_en, warnings_he)
- prescriptions(presc_id, user_id, med_id, refills_left, status)
- inventory(store_id, med_id, qty, restock_eta)

Seed strategy:

- Deterministic seed script in scripts/seed_db.py creates required rows and sample scenarios (in-stock/out-of-stock, multiple prescriptions).

### 2.5 Evaluation & Testing (MVP)

We will provide an evaluation plan for flows.
Testing rigor should include Hebrew coverage and multiple variations per flow.

Plan:

- For each of 3 flows:
  - 2–3 test variations (e.g., NOT_FOUND, AMBIGUOUS, OUT_OF_STOCK)
  - At least one Hebrew and one English test case per flow
- Metrics (lightweight):
  - Flow completion rate
  - Policy adherence rate (correct refusals)
  - Tool-call success/error rate

### 2.6 Packaging & Runbook

Deliverables include Dockerfile + README + screenshots.

- README.md: architecture summary + how to run locally and via Docker
- Docker:
  - Single image that serves API + UI (preferred for MVP simplicity)
- uv:
  - Dependencies pinned in pyproject.toml
  - Document the uv install/sync/run commands in README

### 2.7 Suggested Repo Layout (MVP)

- apps/api/ — FastAPI app + LangGraph agent + tools
- apps/web/ — static UI (index.html, app.js, style.css)
- scripts/ — DB seed
- docs/ — this spec + flow definitions + eval plan
- tests/ — tool unit tests + flow integration tests
- pyproject.toml — uv-managed deps
- Dockerfile

---

## 3) Deliverables Checklist (MVP)

- README with architecture + Docker run instructions
- 3 multi-step flow demonstrations
- 2–3 screenshots of conversations (include at least one Hebrew)
- Evaluation plan for the agent flows
