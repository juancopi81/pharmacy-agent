FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY apps/ ./apps/
COPY scripts/ ./scripts/

# Install dependencies
RUN uv sync --frozen --no-dev

# Create data directory and seed database
RUN mkdir -p data && uv run python scripts/seed_db.py

# Expose port
EXPOSE 8000

# Run server
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
