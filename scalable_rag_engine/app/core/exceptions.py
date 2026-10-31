from typing import Any
from fastapi import status

class AppException(Exception):
    """Base application exception for domain errors."""
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_400_BAD_REQUEST, 
        error_code: str = "BAD_REQUEST",
        details: Any = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details

class EntityNotFoundException(AppException):
    def __init__(self, message: str = "Requested resource not found."):
        super().__init__(
            message=message, 
            status_code=status.HTTP_404_NOT_FOUND, 
            error_code="NOT_FOUND"
        )

class AccessDeniedError(AppException):
    def __init__(self, message: str = "Access denied."):
        super().__init__(
            message=message, 
            status_code=status.HTTP_403_FORBIDDEN, 
            error_code="FORBIDDEN"
        )
        