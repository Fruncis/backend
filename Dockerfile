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

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

EXPOSE 8000

# The entrypoint runs Alembic migrations then starts uvicorn.
# Secrets (GEMINI_API_KEY, etc.) are injected at runtime via environment
# variables — they are NEVER baked into the image.
ENTRYPOINT ["./entrypoint.sh"]
