from fastapi import FastAPI

from routers.consent import router as consent_router
from routers.documents import router as documents_router
from routers.packet import router as packet_router
from routers.rules import router as rules_router

app = FastAPI()
app.include_router(consent_router)
app.include_router(documents_router)
app.include_router(rules_router)
app.include_router(packet_router)


@app.get("/health")
def health():
    return {"status": "ok"}
