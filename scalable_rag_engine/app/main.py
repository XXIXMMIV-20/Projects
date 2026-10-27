from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine , Base
from app.models.domain import User, Document

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Scalable RAG Engine", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected" }
