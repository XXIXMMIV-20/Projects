import asyncio
from pathlib import Path
from pypdf import PdfReader
from app.core.database import AsyncSessionLocal
from app.models.domain import DocumentStatus
from app.crud import repository

def extract_text_sync(file_path: Path) -> str:
    """
    Synchronous helper to extract text from PDF or plain text files. 
    Executed inside a worker thread via asyncio.to_thread to avoid blocking the event loop.
    """
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(str(file_path))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages_text).strip()
    else:
        return file_path.read_text(encoding="utf-8").strip()

def chunk_text_sliding_window(
        text: str,
        chunk_size: int = 800,
        chunk_overlap: int = 150
) -> list[str]:
    """
    Splits text into overlapping chunks so semantic context isn't lost at boundaries.
    """
    if not text:
        return []

    cleaned_text = " ".join(text.split())
    if len(cleaned_text) <= chunk_size:
        return [cleaned_text]
    chunks = []
    step = chunk_size - chunk_overlap
    for start in range(0, len(cleaned_text), step):
        chunk = cleaned_text[start:start + chunk_size]
        chunks.append(chunk)
        if start + chunk_size >= len(cleaned_text):
            break
    return chunks

async def process_document_task(doc_id: str, file_path: Path):
    """
    Background worker that extracts text, creates overlapping chunks, and persists them.
    """
    async with AsyncSessionLocal() as db:
        try:
            await repository.update_document_status(
                db, doc_id=doc_id, status=DocumentStatus.PROCESSING
            )

            if not file_path.exists():
                        raise FileNotFoundError(f"Uploaded file not found at {file_path}")
            
            raw_text = await asyncio.to_thread(extract_text_sync, file_path)
            if not raw_text:
                raise ValueError("No extractable text found in document (file may be empty or scanned image)")
    
            text_chunks = chunk_text_sliding_window(raw_text, chunk_size=800, chunk_overlap=150)

            saved_count = await repository.create_document_chunks(
                db, doc_id=doc_id, text_chunks=text_chunks
            )

            await repository.update_document_status(
                db, 
                doc_id=doc_id, 
                status=DocumentStatus.COMPLETED, 
                chunk_count=saved_count
            )
            print(f"✅ Background Ingestion Complete: Doc {doc_id} -> {saved_count} real chunks stored in DB.")

        except Exception as exc:
            await repository.update_document_status(
                db, 
                doc_id=doc_id, 
                status=DocumentStatus.FAILED, 
                error_message=str(exc)
            )
            print(f"❌ Ingestion Failed: Doc {doc_id} -> {exc}")