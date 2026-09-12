"""
Single FastAPI application entrypoint.

Design note: the reference project we reviewed had two competing
entrypoints (app.py and main.py) with overlapping routes. We keep
exactly one app object, and every route lives in app/routers/.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure Postgres tables and Qdrant collection exist.
    from app.services.db import init_db
    from app.services.vector_store import init_vector_store

    init_db()
    init_vector_store()

    yield
    # Shutdown: nothing to clean up yet.


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the React dev server (and later, the deployed frontend) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": settings.environment}


from app.routers import chat, ingestion, metrics  # noqa: E402
 
app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])

# Added in later steps:
# from app.routers import dashboard
# app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)