from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine , Base
from app.models.domain import User, Document
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Scalable RAG Engine", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1", tags=["Core Domain"])

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "database": "connected" }
