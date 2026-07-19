from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401 - registers all tables on Base.metadata before create_all
from config import settings
from db import Base, engine
from routers.consent import router as consent_router
from routers.documents import router as documents_router
from routers.packet import router as packet_router
from routers.rules import router as rules_router
from routers.session import router as session_router

Base.metadata.create_all(bind=engine)

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
