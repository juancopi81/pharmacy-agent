# Pharmacy Agent (MVP)

Run (Docker):

1. Create a `.env` file with `OPENAI_API_KEY` (use the key provided in the assignment email)
2. Build + run:
   - docker build -t pharmacy-agent .
   - docker run --env-file .env -p 8000:8000 pharmacy-agent
3. Open: http://localhost:8000

Docs:

- docs/PROJECT_SPEC.md
- docs/FLOWS.md
- docs/EVAL_PLAN.md
