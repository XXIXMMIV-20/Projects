from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Scalable RAG Engine"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres123@localhost:5432/rag_knowledge_db"

    SECRET_KEY: str = "super-secret-rag-key-change-in-production-9f8a7b6c5d4e"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()