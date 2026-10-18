
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Nigerian Property Valuation API",
    version="1.0.0",
    description=(
        "Transparent indicative property estimates using "
        "comparable records. Educational demonstration only; "
        "not a professional valuation."
    ),
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": "Nigerian Property Valuation API",
    }
