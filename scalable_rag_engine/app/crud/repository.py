from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain import DocumentChunk, User, Document, DocumentStatus
from app.schemas.domain import UserCreate
from app.core.security import hash_password

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    db_user = User(
        email=user_in.email, 
        hashed_password=hash_password(user_in.password)
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

async def get_document_by_id(db: AsyncSession, doc_id: str) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalars().first()

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

async def create_document_chunks(
    db: AsyncSession, 
    doc_id: str,
    text_chunks: list[str]
) -> int:
    chunk_objects = [
        DocumentChunk(
            document_id=doc_id,
            chunk_index=idx,
            content=chunk_text,
            char_count=len(chunk_text)
        )
        for idx, chunk_text in enumerate(text_chunks)
    ]
    db.add_all(chunk_objects)
    await db.commit()
    return len(chunk_objects)

async def get_document_chunks(db: AsyncSession, doc_id: str) -> list[DocumentChunk]:
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(result.scalars().all())

async def delete_document(db: AsyncSession, doc_id: str) -> bool:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalars().first()
    if doc:
        await db.delete(doc)
        await db.commit()
        return True
    return False