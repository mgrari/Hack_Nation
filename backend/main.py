from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401 - registers all tables on Base.metadata before create_all
import rules_rag
from config import settings
from db import Base, engine
from routers.consent import router as consent_router
from routers.documents import router as documents_router
from routers.packet import router as packet_router
from routers.rules import router as rules_router
from routers.session import router as session_router

# NOTE: create_all() only creates tables that don't exist yet -- it never ALTERs an
# existing table. This project has no migration framework by design (kept out on
# purpose), so if a model gains/changes a column (e.g. DocumentRecord.document_type)
# after a table has already been created in a persistent environment (e.g. Render's
# production Postgres), that column will silently never appear there. Fix by manually
# running the equivalent ALTER TABLE, or by resetting the DB, in that environment.
Base.metadata.create_all(bind=engine)

# Re-ingest the rule corpus on every startup so /ask always serves the current contents
# of data/rules/organizer_rule_corpus.jsonl -- ingest_corpus() resets the collection each
# time, so this can't drift the way a one-off manual ingestion script would.
rules_rag.ingest_corpus()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(consent_router)
app.include_router(documents_router)
app.include_router(rules_router)
app.include_router(packet_router)
app.include_router(session_router)


@app.get("/health")
def health():
    return {"status": "ok"}
