"""
FastAPI dependencies.

This module defines reusable dependencies for authentication, database sessions,
and role-based access control.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.models.user import User, UserRole
from api.services.auth_service import AuthService


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[Optional[str], Cookie(alias=settings.COOKIE_NAME)] = None,
) -> User:
    """
    Dependency to get the current authenticated user from JWT cookie.
    
    Args:
        db: Database session.
        access_token: JWT token from cookie.
        
    Returns:
        Authenticated User.
        
    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 401: If user not found or inactive.
    """
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login first.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = AuthService.decode_token(access_token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await AuthService.get_user_by_id(db, token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[Optional[str], Cookie(alias=settings.COOKIE_NAME)] = None,
) -> Optional[User]:
    """
    Dependency to optionally get the current authenticated user.
    
    Returns None instead of raising exception if not authenticated.
    
    Args:
        db: Database session.
        access_token: JWT token from cookie.
        
    Returns:
        User if authenticated, None otherwise.
    """
    if access_token is None:
        return None
    
    token_data = AuthService.decode_token(access_token)
    
    if token_data is None:
        return None
    
    user = await AuthService.get_user_by_id(db, token_data.user_id)
    
    if user is None or not user.is_active:
        return None
    
    return user


def require_role(required_roles: list[UserRole]):
    """
    Factory function to create a dependency that requires specific roles.
    
    Args:
        required_roles: List of allowed roles.
        
    Returns:
        Dependency function that validates user role.
        
    Example:
        ```python
        @router.post("/admin-only")
        async def admin_endpoint(
            user: User = Depends(require_role([UserRole.ADMIN]))
        ):
            pass
        ```
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {[r.value for r in required_roles]}",
            )
        return current_user
    
    return role_checker


# Pre-built role dependencies
require_viewer = require_role([UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN])
require_operator = require_role([UserRole.OPERATOR, UserRole.ADMIN])
require_admin = require_role([UserRole.ADMIN])


# Type aliases for cleaner code
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
ViewerUser = Annotated[User, Depends(require_viewer)]
OperatorUser = Annotated[User, Depends(require_operator)]
AdminUser = Annotated[User, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


# Pagination parameters
class PaginationParams:
    """Common pagination parameters."""
    
    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
        size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 10,
    ):
        self.page = page
        self.size = size


Pagination = Annotated[PaginationParams, Depends()]
