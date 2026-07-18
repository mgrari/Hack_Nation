from fastapi import FastAPI

from routers.consent import router as consent_router

app = FastAPI()
app.include_router(consent_router)


@app.get("/health")
def health():
    return {"status": "ok"}
