from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models.domain import DocumentStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    user_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    char_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
