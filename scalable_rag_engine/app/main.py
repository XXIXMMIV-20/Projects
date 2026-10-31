import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.database import engine
from app.core.logging_config import setup_logging
from app.core.exceptions import AppException
from app.api.routes import router as api_router

setup_logging()
logger = logging.getLogger("rag_engine")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up with Alembic migrations enabled.")
    yield
    await engine.dispose()
    logger.info("Application shutdown complete.")

app = FastAPI(title="Scalable RAG Engine", lifespan=lifespan)

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            f"HTTP {request.method} {request.url.path} completed with status {response.status_code} in {duration_ms}ms",
            extra={"request_id": request_id}
        )
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            f"Unhandled exception during {request.method} {request.url.path} after {duration_ms}ms: {exc}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        raise exc

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id   
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", None)
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}", extra={"request_id": req_id})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload.",
                "details": exc.errors(),
                "request_id": req_id
            }
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "request_id": req_id
            }
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", None)
    logger.error(f"Internal server error: {exc}", exc_info=True, extra={"request_id": req_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
                "details": None,
                "request_id": req_id
            }
        }
    )

app.include_router(api_router, prefix="/api/v1", tags=["Core Domain"])

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "database": "connected" }
