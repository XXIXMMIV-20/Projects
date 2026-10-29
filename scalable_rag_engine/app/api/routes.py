import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.domain import UserCreate, UserResponse, DocumentResponse, DocumentChunkResponse
from app.crud import repository
from app.services.ingestion import process_document_task
from app.core.security import verify_password

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await repository.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    return await repository.create_user(db, user_in=user_in)

@router.post("/users/login", response_model=UserResponse)
async def login_user(credentials: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await repository.get_user_by_email(db, email=credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    return user

@router.post("/users/{user_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_user_document(
    user_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    user = await repository.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
        )

    temp_path = UPLOAD_DIR / f"temp_{file.filename}"
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size_bytes = temp_path.stat().st_size

    doc = await repository.create_document(
        db,
        filename=file.filename or "untitled",
        file_size_bytes=file_size_bytes,
        user_id=user_id
    )

    final_path = UPLOAD_DIR / f"{doc.id}_{file.filename}"
    temp_path.rename(final_path)

    background_tasks.add_task(process_document_task, doc.id, final_path)

    return doc

@router.get("/users/{user_id}/documents", response_model=list[DocumentResponse])
async def list_user_documents(user_id: str, db: AsyncSession = Depends(get_db)):
    return await repository.get_user_documents(db, user_id=user_id)

@router.get("/documents/{doc_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_chunks_for_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    return await repository.get_document_chunks(db, doc_id=doc_id)

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    success = await repository.delete_document(db, doc_id=doc_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return None