# Pharmacy Agent (MVP)

Real-time AI pharmacy agent for medication info, inventory checks, and prescription management.

## Quick Start (Local)

```bash
# 1. Install dependencies
uv sync

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Seed the database
uv run python scripts/seed_db.py

# 4. Run the server
uv run uvicorn apps.api.main:app --reload --port 8000

# 5. Open http://localhost:8000
```

## Database

Seed creates SQLite database at `data/pharmacy.db` with:
- 10 users (phone + email)
- 5 medications (Hebrew + English)
- 8 prescriptions (varied scenarios)
- Inventory (in-stock, low-stock, out-of-stock)

```bash
# Re-seed (resets all data)
uv run python scripts/seed_db.py

# Verify data
sqlite3 data/pharmacy.db ".tables"
sqlite3 data/pharmacy.db "SELECT name_en, name_he FROM medications;"
```

## Run (Docker)

```bash
docker build -t pharmacy-agent .
docker run --env-file .env -p 8000:8000 pharmacy-agent
```

## Docs

- [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) - Full spec
- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) - Progress tracking
- [docs/FLOWS.md](docs/FLOWS.md) - Multi-step flows
- [docs/EVAL_PLAN.md](docs/EVAL_PLAN.md) - Evaluation plan
