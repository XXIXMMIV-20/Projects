from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.domain import UserCreate, UserResponse, DocumentResponse
from app.crud import repository

router = APIRouter()

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await repository.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A user with this email already exists."
        )
    return await repository.create_user(db, user_in=user_in)

@router.post("/users/{user_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_user_document(
    user_id: str, 
    filename: str, 
    file_size_bytes: int, 
    db: AsyncSession = Depends(get_db)
):
    return await repository.create_document(
        db, filename=filename, file_size_bytes=file_size_bytes, user_id=user_id
    )

@router.get("/users/{user_id}/documents", response_model=list[DocumentResponse])
async def list_user_documents(user_id: str, db: AsyncSession = Depends(get_db)):
    return await repository.get_user_documents(db, user_id=user_id)