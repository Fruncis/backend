# CV Processor — Backend

A Python backend built with **FastAPI** following the **Ports and Adapters (Hexagonal Architecture)** pattern.

> **Before writing any code, read [`ARCHITECTURE.md`](ARCHITECTURE.md).** It is the law of the codebase.

---

## Quick Start

### 1. Create and activate the virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Copy and configure environment variables

```bash
cp .env.example .env
# Then open .env and set GEMINI_API_KEY to your real key
```

### 4. Run Alembic migrations

```bash
alembic upgrade head
```

### 5. Start the server

```bash
python main.py
```

The server will start on `http://0.0.0.0:8000` by default (configurable in `config.yaml`).

---

## Project Structure

```
backend/
├── ARCHITECTURE.md          ← read this first
├── config.yaml              ← runtime configuration
├── main.py                  ← composition root
├── requirements.txt
├── .env.example
│
├── core/                    ← pure business logic (no framework deps)
│   ├── config/              ← Pydantic settings loader
│   ├── domain/              ← entities, value objects, exceptions
│   ├── ports/               ← abstract interfaces (ABCs)
│   └── usecases/            ← orchestration (uses ports only)
│
├── adapters/                ← infrastructure glue
│   ├── inbound/
│   │   └── fastapi/         ← HTTP API routers
│   └── outbound/
│       ├── postgres/        ← database adapter
│       └── gemini/          ← Gemini AI adapter
│
├── prompts/                 ← prompt templates
│   └── cv_parsing.txt
│
└── migrations/              ← Alembic migration scripts
```

---

## Important Notes

- **Virtual environment (`.venv/`)** is already in `.dockerignore` and should be added to `.gitignore`. It must **never** be committed to Git.
- The Golden Rule: **`core/` must never import from `adapters/`** — see `ARCHITECTURE.md` for details.
- This project uses `google-genai` (not the deprecated `google-generativeai`).
