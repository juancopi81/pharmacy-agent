# Project Status

## Milestones

### M0 — Repo + Scaffolding
- [x] Python/FastAPI skeleton
- [x] uv config (pyproject.toml)
- [ ] Basic UI stub (apps/web/)

### M1 — Data Layer
- [ ] SQLite schema design
- [ ] Seed script (scripts/seed_db.py)
- [ ] 10 users, 5 medications, sample prescriptions, inventory

### M2 — Tools
- [ ] Tool 1: `get_medication_by_name`
- [ ] Tool 2: `check_inventory`
- [ ] Tool 3: `prescription_management`
- [ ] Document schemas/errors/fallbacks for each tool

### M3 — Agent Orchestration + Streaming
- [ ] LangGraph workflow setup
- [ ] POST /chat/stream endpoint
- [ ] SSE streaming responses
- [ ] Bilingual support (Hebrew + English)

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

- [ ] Stateless backend (client sends history each turn)
- [ ] Real-time text streaming (GPT-5)
- [ ] Hebrew and English support
- [ ] At least 3 tools with clear API design
- [ ] Synthetic DB (10 users, 5 medications)
- [ ] UI to interact with the agent
- [ ] At least 3 distinct multi-step flows
- [ ] Policy enforcement (facts-only, no medical advice)
