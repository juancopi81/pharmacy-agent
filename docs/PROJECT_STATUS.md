# Project Status

## Milestones

### M0 — Repo + Scaffolding
- [x] Python/FastAPI skeleton (apps/api/main.py + config + schemas + logging)
- [x] uv config (pyproject.toml)
- [x] Chat UI (apps/web/index.html, app.js, style.css)

### M1 — Data Layer
- [x] SQLite schema design (users, medications, prescriptions, inventory)
- [x] Seed script (scripts/seed_db.py)
- [x] 10 users, 5 medications, 8 prescriptions, inventory
- [x] Database helper (apps/api/database.py)

### M2 — Tools
- [x] Tool 1: `get_medication_by_name` (apps/api/tools/medication.py)
- [x] Tool 2: `check_inventory` (apps/api/tools/inventory.py)
- [x] Tool 3: `prescription_management` (apps/api/tools/prescription.py)
- [x] Document schemas/errors/fallbacks (apps/api/tools/schemas.py, exceptions.py)
- [x] Unit tests (24 tests passing)

### M3 — Agent Orchestration + Streaming
- [x] LangGraph workflow setup (apps/api/agent/)
- [x] POST /chat/stream endpoint with agent integration
- [x] SSE streaming responses (token, tool_call, tool_result, error, done events)
- [x] Bilingual support via system prompt (Hebrew + English)

### M4 — Flows + Evaluation
- [ ] Flow A: Medication Info (Customer Service)
- [ ] Flow B: Inventory Check (Inventory Control)
- [ ] Flow C: Prescription Status/Refill (Prescription Management)
- [ ] Test cases (EN + HE coverage)
- [ ] Policy adherence tests (refuse advice/diagnosis)

### M5 — Packaging + Evidence
- [ ] Dockerfile
- [ ] README with run instructions
- [ ] 2-3 screenshots of conversations (at least one Hebrew)

## Deliverables Checklist

- [ ] README.md with architecture + Docker run instructions
- [ ] 3 multi-step flow demonstrations
- [ ] 2-3 screenshots of conversations
- [ ] Evaluation plan for agent flows (docs/EVAL_PLAN.md)
- [ ] Dockerfile

## Technical Requirements

- [x] Stateless backend (client sends history each turn)
- [x] Real-time text streaming (GPT-5)
- [x] Hebrew and English support
- [x] At least 3 tools with clear API design
- [x] Synthetic DB (10 users, 5 medications)
- [x] UI to interact with the agent
- [ ] At least 3 distinct multi-step flows
- [x] Policy enforcement (facts-only, no medical advice)
