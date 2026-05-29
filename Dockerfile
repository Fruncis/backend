# ── Stage: runtime ───────────────────────────────────────────────────────
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
# so container logs appear in real time.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Dependencies (cached layer — only re-runs when requirements change) ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ────────────────────────────────────────────────────
COPY . .

EXPOSE 8000

# The entrypoint runs Alembic migrations then starts uvicorn.
# Using a python script avoids CRLF line-ending issues when building on Windows
# and allows it to run natively on both Windows (local) and Linux (Docker).
# Secrets are injected at runtime via environment variables.
ENTRYPOINT ["python", "entrypoint.py"]
