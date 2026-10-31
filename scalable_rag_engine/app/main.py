from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(title="Scalable RAG Engine", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1", tags=["Core Domain"])

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "database": "connected" }
