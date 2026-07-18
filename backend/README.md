# RealDoor — Backend

FastAPI service for the RealDoor application-readiness copilot. Handles document
extraction, rules retrieval (RAG), deterministic MTSP calculations, and packet
preparation. See the [root README](../README.md) for the full challenge brief.

## What lives here

| Path | Purpose |
|---|---|
| `main.py` | FastAPI app entrypoint. Currently exposes a `/health` check; API routes get added here. |
| `requirements.txt` | Pinned Python dependencies. |
| `.env` | Local secrets and config (not for commit — see [Configuration](#configuration)). |
| `venv/` | Local virtualenv (git-ignored; do not commit). |

Related data (rule corpus, gold checklists, synthetic documents) lives in the
top-level [`../data/`](../data) directory.

### Key dependencies

- **fastapi** + **uvicorn** — web framework and ASGI server.
- **chromadb** — vector store for the cited rules corpus.
- **openai** — LLM calls for extraction and Q&A.
- **pypdf** — parse uploaded synthetic documents.
- **pandas** + **openpyxl** — parse HUD's static MTSP income-limit Excel file (used by `../fetch_hud_data.py`).
- **SQLAlchemy** + **psycopg2-binary** — persistence on Postgres (profiles, consent/action logs). Deployed on Render alongside the backend.

## Setup

Requires **Python 3.11+**.

```bash
cd backend

# create + activate a virtualenv
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in this directory:

```env
OPENAI_API_KEY=sk-...                                   # your OpenAI key
DATABASE_URL=postgresql://user:password@localhost:5432/realdoor
```

For local development without a Postgres server running, point `DATABASE_URL` at a local instance (e.g. `docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres`). Production uses a Render-managed Postgres instance.

`.env` holds secrets — keep it out of version control.

## Run

```bash
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Interactive docs: http://localhost:8000/docs

## Freezing dependencies

After adding a package, re-pin:

```bash
pip freeze > requirements.txt
```
