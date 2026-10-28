import asyncio
from pathlib import Path
from app.core.database import AsyncSessionLocal
from app.models.domain import DocumentStatus
from app.crud import repository

async def process_document_task(doc_id: str, file_path: Path):
    """
    Background worker that manages the document ingestion state machine.
    Uses its own isolated AsyncSession since the HTTP request session is already closed.
    """
    async with AsyncSessionLocal() as db:
        try:
            await repository.update_document_status(
                db, doc_id=doc_id, status=DocumentStatus.PROCESSING
            )

            await asyncio.sleep(2)  

            if not file_path.exists():
                raise FileNotFoundError(f"Uploaded file not found at {file_path}")

            size_bytes = file_path.stat().st_size
            estimated_chunks = max(1, size_bytes // 500)

            await repository.update_document_status(
                db, 
                doc_id=doc_id, 
                status=DocumentStatus.COMPLETED, 
                chunk_count=estimated_chunks
            )
            print(f"✅ Background Ingestion Complete: Doc {doc_id} ({estimated_chunks} chunks)")

        except Exception as exc:
            await repository.update_document_status(
                db, 
                doc_id=doc_id, 
                status=DocumentStatus.FAILED, 
                error_message=str(exc)
            )
            print(f"❌ Background Ingestion Failed: Doc {doc_id} -> {exc}")