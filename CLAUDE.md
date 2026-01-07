# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MVP AI pharmacy agent that provides real-time conversational assistance using GPT-5 and LangGraph. The agent handles prescription management, inventory control, and customer service through a stateless, streaming chat interface supporting Hebrew and English.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the application locally
uv run uvicorn apps.api.main:app --reload --port 8000

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_file.py::test_name -v

# Seed the database
uv run python scripts/seed_db.py
```

## Docker

```bash
docker build -t pharmacy-agent .
docker run --env-file .env -p 8000:8000 pharmacy-agent
```

## Architecture

### Tech Stack
- **Backend**: Python + FastAPI
- **Agent Orchestration**: LangGraph (graph-based workflow for multi-step flows + tool routing)
- **LLM**: OpenAI API (GPT-5)
- **Streaming**: HTTP SSE (text/event-stream)
- **Database**: SQLite (synthetic seeded dataset)
- **UI**: Static HTML + vanilla JS served by FastAPI
- **Package Management**: uv + pyproject.toml

### Repo Layout
- `apps/api/` — FastAPI app + LangGraph agent + tools
- `apps/web/` — Static UI (index.html, app.js, style.css)
- `scripts/` — DB seed script
- `docs/` — Specs, flow definitions, eval plan
- `tests/` — Tool unit tests + flow integration tests

### Key Design Decisions

1. **Stateless Backend**: No server-side session storage. Client sends conversation history each turn via POST /chat/stream.

2. **Three Core Tools**:
   - `get_medication_by_name`: Resolve medication by EN/HE name, return factual fields
   - `check_inventory`: Check stock for medication at a store
   - `prescription_management`: User prescription workflows (LIST, REFILL_STATUS)

3. **Three Multi-Step Flows**:
   - Flow A (Medication Info): Resolve medication → Return factual info → Refuse advice requests
   - Flow B (Inventory Check): Resolve medication → Check inventory → Return availability
   - Flow C (Prescription Status/Refill): Get user identifier → Retrieve prescriptions → Handle refill/status

4. **Bilingual**: Respond in same language as user's message (Hebrew ↔ English)

5. **Policy Constraints**: Facts-only responses, no medical advice/diagnosis, no purchase encouragement

### Database Schema (SQLite)
- `users(user_id, name, phone, email)` — 10 synthetic users
- `medications(med_id, name_en, name_he, active_ingredients, dosage_en, dosage_he, rx_required, warnings_en, warnings_he)` — 5 medications
- `prescriptions(presc_id, user_id, med_id, refills_left, status)`
- `inventory(store_id, med_id, qty, restock_eta)`

### API Endpoints
- `GET /` — Serves the chat UI
- `POST /chat/stream` — Streaming chat endpoint
  - Input: `messages[]`, optional `user_identifier`, optional `lang_mode`
  - Output: SSE stream with token events and tool events

## Documentation

- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) — Implementation checklist and progress tracking
- [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) — Full PRD + technical design for the MVP
- [docs/FLOWS.md](docs/FLOWS.md) — Detailed multi-step flow definitions
- [docs/EVAL_PLAN.md](docs/EVAL_PLAN.md) — Evaluation plan for agent flows
- [docs/HOME_ASSIGNMENT.md](docs/HOME_ASSIGNMENT.md) — Original assignment requirements

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY` — OpenAI API key for GPT-5
- Update files in the docs folder after major milestones and major additions to the project