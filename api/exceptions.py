"""
Custom exception handlers.

This module defines custom exceptions and their handlers for the API.
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class APIException(HTTPException):
    """Base API exception with machine-readable code."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str = "ERROR",
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


class NotFoundException(APIException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, identifier: str = ""):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with ID '{identifier}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code="NOT_FOUND",
        )


class ConflictException(APIException):
    """Resource conflict exception (e.g., duplicate)."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            code="CONFLICT",
        )


class BadRequestException(APIException):
    """Bad request exception for business logic errors."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code="BAD_REQUEST",
        )


class UnauthorizedException(APIException):
    """Authentication required exception."""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="UNAUTHORIZED",
        )


class ForbiddenException(APIException):
    """Access forbidden exception."""
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="FORBIDDEN",
        )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handler for APIException that includes machine-readable code."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for standard HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": "HTTP_ERROR",
        },
    )
