# Pharmacy Agent (MVP)

Real-time AI pharmacy agent powered by GPT-5 and LangGraph. Provides medication information, inventory checks, and prescription management through a streaming chat interface supporting Hebrew and English.

## Quick Start (Docker)

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Build and run
docker build -t pharmacy-agent .
docker run --env-file .env -p 8000:8000 pharmacy-agent

# 3. Open http://localhost:8000
```

> For local development without Docker, see [Local Development](#local-development) below.

---

## Key Features

| Feature             | Description                                                 |
| ------------------- | ----------------------------------------------------------- |
| Real-time streaming | SSE-based streaming responses with token-by-token output    |
| Bilingual           | Responds in Hebrew or English based on user's language      |
| 3 Tools             | Medication lookup, inventory check, prescription management |
| 3 Multi-step flows  | Complete customer journeys from request to resolution       |
| Policy enforcement  | Facts-only responses, refuses medical advice                |
| Stateless           | Client sends conversation history each turn                 |

---

## Multi-Step Flows

The agent executes three distinct multi-step flows, each representing a complete customer journey:

### Flow A: Medication Info (Customer Service)

```
User: "Tell me about Ibuprofen"
  → Agent calls get_medication_by_name()
  → Returns: active ingredients, dosage, warnings, Rx status

User: "Should I take it for my headache?"
  → Agent REFUSES medical advice
  → Redirects to healthcare professional
```

### Flow B: Inventory Check (Inventory Control)

```
User: "Do you have Amoxicillin in stock?"
  → Agent calls get_medication_by_name()
  → Agent calls check_inventory()
  → Returns: availability status + restock ETA if out of stock
```

### Flow C: Prescription Management (Multi-turn)

```
User: "What prescriptions do I have?"
  → Agent asks for email/phone identifier

User: "david.cohen@example.com"
  → Agent calls prescription_management(LIST)
  → Returns: list of prescriptions with refill status

User: "Can I refill the Amoxicillin?"
  → Agent calls prescription_management(REFILL_STATUS)
  → Returns: eligibility and refills remaining
```

See [docs/FLOWS.md](docs/FLOWS.md) for detailed sequence diagrams and tool call documentation.

---

## Evaluation

### Test Cases

| ID  | Flow            | Language | Scenario                       | Status |
| --- | --------------- | -------- | ------------------------------ | ------ |
| A1  | Medication Info | EN       | Happy path - medication found  | PASS   |
| A2  | Medication Info | HE       | Hebrew query and response      | PASS   |
| A3  | Medication Info | EN       | NOT_FOUND error handling       | PASS   |
| B1  | Inventory       | EN       | In-stock medication            | PASS   |
| B2  | Inventory       | HE       | Out-of-stock with ETA          | PASS   |
| B3  | Inventory       | EN       | NOT_FOUND error handling       | PASS   |
| C1  | Prescription    | EN       | Multi-turn: list prescriptions | PASS   |
| C2  | Prescription    | HE       | Hebrew prescription status     | PASS   |
| C3  | Prescription    | EN       | UNAUTHORIZED user              | PASS   |
| P1  | Policy          | EN       | Refuse medical advice          | PASS   |
| P2  | Policy          | EN       | Refuse comparative advice      | PASS   |

### Metrics

- **Flow completion rate**: 100% (11/11 test cases)
- **Policy adherence**: 100% (correctly refuses medical advice and comparisons)
- **Bilingual coverage**: Hebrew and English tested per flow
- **Tool-call success**: All tools execute correctly with proper error handling

See [docs/EVAL_PLAN.md](docs/EVAL_PLAN.md) for full evaluation methodology.

---

## Screenshots (Evidence)

Screenshots demonstrating all flows are in `docs/screenshots/`:

| Screenshot                                     | Description                                                     |
| ---------------------------------------------- | --------------------------------------------------------------- |
| `test_A1_medication_info_en_no_activity.png`   | English medication lookup (Ibuprofen)                           |
| `test_A1_medication_info_en_show_activity.png` | English medication lookup (Ibuprofen) - Shows internal activity |
| `test_A2_medication_info_he.png`               | Hebrew medication lookup (Cetirizine)                           |
| `test_A3_medication_not_found_en.png`          | English medication lookup (XYZMed) - Not found                  |
| `test_B1_inventory_en.png`                     | English inventory check (in-stock + Quantity)                   |
| `test_B2_inventory_he.png`                     | Hebrew inventory check (out-of-stock + ETA)                     |
| `test_C1_prescription_flow.png`                | Multi-turn prescription flow                                    |
| `test_P1_policy_refusal.png`                   | Policy enforcement (refuses medical advice)                     |
| `test_P2_policy_comparison.png`                | Policy enforcement (refuses comparative advice)                 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (Chat UI)                        │
│  - Stores conversation history                              │
│  - Renders streaming tokens                                 │
│  - Sends POST /chat/stream                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Backend (Stateless)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LangGraph Agent (ReAct)                │   │
│  │  - System prompt with policy enforcement            │   │
│  │  - Bilingual (responds in user's language)          │   │
│  │  - GPT-5 with streaming                             │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                    │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │                   3 Tools                           │   │
│  │  • get_medication_by_name (EN/HE lookup)            │   │
│  │  • check_inventory (stock + ETA)                    │   │
│  │  • prescription_management (LIST, REFILL_STATUS)    │   │
│  └─────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                SQLite Database (data/pharmacy.db)           │
│  • 10 users       • 5 medications (EN + HE)                 │
│  • 8 prescriptions (varied scenarios)                       │
│  • Inventory (in-stock, low-stock, out-of-stock)            │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

- **Backend**: Python + FastAPI
- **Agent**: LangGraph (ReAct pattern)
- **LLM**: OpenAI GPT-5
- **Streaming**: Server-Sent Events (SSE)
- **Database**: SQLite
- **UI**: Vanilla HTML/JS
- **Package Manager**: uv

---

## Project Structure

```
pharmacy-agent/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── agent/              # LangGraph agent + streaming
│   │   │   ├── graph.py        # Agent creation
│   │   │   ├── prompts.py      # System prompts
│   │   │   └── streaming.py    # SSE adapter
│   │   ├── tools/              # 3 pharmacy tools
│   │   │   ├── medication.py   # get_medication_by_name
│   │   │   ├── inventory.py    # check_inventory
│   │   │   └── prescription.py # prescription_management
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Settings
│   │   └── database.py         # DB helpers
│   └── web/                    # Static chat UI
│       ├── index.html
│       ├── app.js
│       └── style.css
├── data/
│   └── pharmacy.db             # SQLite database
├── docs/
│   ├── FLOWS.md                # Multi-step flow documentation
│   ├── EVAL_PLAN.md            # Evaluation plan + test cases
│   ├── PROJECT_SPEC.md         # Full PRD + technical design
│   ├── PROJECT_STATUS.md       # Implementation progress
│   └── screenshots/            # Evidence screenshots
├── scripts/
│   └── seed_db.py              # Database seeding
├── tests/
│   └── test_tools/             # 24 unit tests
├── pyproject.toml              # Dependencies (uv)
└── Dockerfile                  # Container build
```

---

## Database

The seed script creates `data/pharmacy.db` with synthetic data for testing all flows.

### Business Rules

| Rule | Logic |
|------|-------|
| **Refill eligibility** | `status = active` AND `refills_left > 0` |
| **Prescription statuses** | `active` (can refill), `completed` (no refills left), `expired` (needs new Rx) |
| **User lookup** | By email or phone number (case-insensitive for email) |
| **Inventory** | Single store (store_id=1), includes restock ETA for out-of-stock items |

### Medications (5)

| Name (EN)   | Name (HE)   | Rx Required | Stock               |
| ----------- | ----------- | ----------- | ------------------- |
| Ibuprofen   | איבופרופן   | No (OTC)    | 150                 |
| Amoxicillin | אמוקסיצילין | Yes         | 0 (ETA: 2026-01-15) |
| Omeprazole  | אומפרזול    | No (OTC)    | 75                  |
| Metformin   | מטפורמין    | Yes         | 5 (low)             |
| Cetirizine  | צטיריזין    | No (OTC)    | 200                 |

### Users with Prescriptions

| User            | Email                   | Prescriptions                                  | Test Scenario |
| --------------- | ----------------------- | ---------------------------------------------- | ------------- |
| David Cohen     | david.cohen@example.com | Amoxicillin (2 refills), Metformin (5 refills) | Happy path - eligible for refill |
| Sarah Levi      | sarah.levi@example.com  | Amoxicillin (completed)                        | No refills remaining |
| Yossi Goldstein | yossi.g@example.com     | Metformin (expired)                            | Expired prescription |

> **Note:** 10 users total are seeded; 7 have no prescriptions (for UNAUTHORIZED testing).

### Schema

```
users(user_id, name, phone, email)
medications(med_id, name_en, name_he, active_ingredients, dosage_en, dosage_he, rx_required, warnings_en, warnings_he)
prescriptions(presc_id, user_id, med_id, refills_left, status)
inventory(store_id, med_id, qty, restock_eta)
```

For detailed tool behavior and edge cases, see [docs/FLOWS.md](docs/FLOWS.md). For implementation, see [`apps/api/tools/`](apps/api/tools/).

```bash
# Re-seed database
uv run python scripts/seed_db.py

# Verify data
sqlite3 data/pharmacy.db "SELECT name_en, name_he FROM medications;"
```

---

## Local Development

For development without Docker:

```bash
# 1. Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Seed the database
uv run python scripts/seed_db.py

# 4. Run the server (with hot reload)
uv run uvicorn apps.api.main:app --reload --port 8000

# 5. Open http://localhost:8000
```

---

## Run Tests

```bash
# Run all unit tests (24 tests)
uv run pytest

# Run specific test file
uv run pytest tests/test_tools/test_medication.py -v
```

---

## API

### POST /chat/stream

Streaming chat endpoint for conversational AI interactions.

**Request:**

```json
{
  "messages": [{ "role": "user", "content": "Tell me about Ibuprofen" }],
  "user_identifier": "david.cohen@example.com" // optional
}
```

**Response:** Server-Sent Events stream

```
data: {"type": "token", "content": "Here's"}
data: {"type": "token", "content": " what"}
data: {"type": "tool_call", "name": "get_medication_by_name", "args": {...}}
data: {"type": "tool_result", "name": "get_medication_by_name", "result": {...}}
data: {"type": "done"}
```

---

## Documentation

| Document                                         | Description                               |
| ------------------------------------------------ | ----------------------------------------- |
| [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md)     | Full PRD + technical design               |
| [docs/FLOWS.md](docs/FLOWS.md)                   | Multi-step flow definitions with examples |
| [docs/EVAL_PLAN.md](docs/EVAL_PLAN.md)           | Evaluation methodology + test cases       |
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | Implementation progress tracking          |
