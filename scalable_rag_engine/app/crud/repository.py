from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain import User, Document
from app.schemas.domain import UserCreate

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    db_user = User(
        email=user_in.email, 
        hashed_password=f"{user_in.password}_hashed_secure"
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def create_document(db: AsyncSession, filename: str, file_size_bytes: int, user_id: str) -> Document:
    db_doc = Document(
        filename=filename,
        file_size_bytes=file_size_bytes,
        user_id=user_id
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    return db_doc

async def get_user_documents(db: AsyncSession, user_id: str) -> list[Document]:
    result = await db.execute(select(Document).where(Document.user_id == user_id))
    return list(result.scalars().all())

async def update_document_status(
        db: AsyncSession, 
        doc_id: str,
        status: str,
        chunk_count: int = 0,
        error_message: str | None = None
) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalars().first()
    if doc:
        doc.status = status
        doc.chunk_count = chunk_count
        doc.error_message = error_message
        await db.commit()
        await db.refresh(doc)
    return doc