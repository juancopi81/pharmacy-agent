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
- [x] Flow A: Medication Info (Customer Service) - documented in docs/FLOWS.md, tested
- [x] Flow B: Inventory Check (Inventory Control) - documented in docs/FLOWS.md, tested
- [x] Flow C: Prescription Status/Refill (Prescription Management) - documented in docs/FLOWS.md, tested
- [x] Test cases (EN + HE coverage) - documented in docs/EVAL_PLAN.md
- [x] Policy adherence tests (refuse advice/diagnosis) - tested and verified

### M5 — Packaging + Evidence
- [x] Dockerfile
- [x] README with run instructions
- [x] 2-3 screenshots of conversations (docs/screenshots/) - includes Hebrew

## Deliverables Checklist

- [x] README.md with architecture + Docker run instructions
- [x] 3 multi-step flow demonstrations (docs/FLOWS.md)
- [x] 2-3 screenshots of conversations (docs/screenshots/)
- [x] Evaluation plan for agent flows (docs/EVAL_PLAN.md)
- [x] Dockerfile

## Technical Requirements

- [x] Stateless backend (client sends history each turn)
- [x] Real-time text streaming (GPT-5)
- [x] Hebrew and English support
- [x] At least 3 tools with clear API design
- [x] Synthetic DB (10 users, 5 medications)
- [x] UI to interact with the agent
- [x] At least 3 distinct multi-step flows (docs/FLOWS.md)
- [x] Policy enforcement (facts-only, no medical advice)

## Post-Review Improvements

Based on code review feedback, the following production-readiness improvements were implemented:

### Architecture
- [x] **Agent singleton pattern**: LangGraph agent now compiled once at startup instead of per-request, reducing overhead
- [x] **API key validation moved**: Validation moved from config init to endpoint, allowing tests to run without API key

### Robustness
- [x] **Streaming chunk parsing hardened**: Added `_extract_chunk_text()` helper to handle various content formats (string, list of strings, list of content-part dicts)
- [x] **CancelledError handling**: Explicit handling prevents client disconnects from polluting error logs

### Documentation
- [x] **README SSE format fixed**: Corrected payload structure to match actual implementation
- [x] **Testing section added**: Documented pytest and auto-eval commands

### Evaluation
- [x] **Automated evaluation script**: Added `scripts/run_eval.py` with LLM-as-Judge pattern for verifying agent behavior
