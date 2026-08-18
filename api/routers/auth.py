"""
Authentication router.

This module defines endpoints for user registration, login, logout, and profile management.
JWT tokens are stored in HTTP-only cookies for security.
"""

from fastapi import APIRouter, Depends, Response, status

from api.config import settings
from api.dependencies import CurrentUser, DbSession
from api.exceptions import BadRequestException, ConflictException, UnauthorizedException
from api.schemas.auth import LoginResponse, UserCreate, UserLogin, UserResponse, UserUpdate
from api.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="POST /api/v1/auth/register - Register a new user",
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "Username or email already exists"},
        422: {"description": "Validation error"},
    },
)
async def register(
    user_data: UserCreate,
    db: DbSession,
) -> UserResponse:
    """
    Register a new user account.

    **Request Body:**
    - `username` (str, required): Unique username. 3-50 characters.
    - `email` (str, required): Valid email address.
    - `password` (str, required): Password. 8-100 characters.
    - `role` (str, optional): User role. Default: "viewer".

    **Response 201:** User created successfully.
    **Response 409:** Username or email already exists.
    **Response 422:** Request body validation failed.
    """
    # Check for existing username
    if await AuthService.check_username_exists(db, user_data.username):
        raise ConflictException(
            f"Username '{user_data.username}' is already taken")

    # Check for existing email
    if await AuthService.check_email_exists(db, user_data.email):
        raise ConflictException(
            f"Email '{user_data.email}' is already registered")

    user = await AuthService.create_user(db, user_data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="POST /api/v1/auth/login - Login and get JWT cookie",
    responses={
        200: {"description": "Login successful, JWT cookie set"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
async def login(
    credentials: UserLogin,
    response: Response,
    db: DbSession,
) -> LoginResponse:
    """
    Authenticate user and set JWT cookie.

    **Request Body:**
    - `username` (str, required): Username or email.
    - `password` (str, required): User password.

    **Response 200:** Login successful. JWT token set as HTTP-only cookie.
    **Response 401:** Invalid username/email or password.
    **Response 422:** Request body validation failed.

    The JWT token is stored in an HTTP-only cookie named 'access_token'.
    This cookie is automatically sent with subsequent requests.
    """
    user = await AuthService.authenticate_user(
        db, credentials.username, credentials.password
    )

    if user is None:
        raise UnauthorizedException("Invalid username or password")

    # Create JWT token
    access_token = AuthService.create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    # Set cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return LoginResponse(
        message="Login successful",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="POST /api/v1/auth/logout - Logout and clear JWT cookie",
    responses={
        200: {"description": "Logout successful, cookie cleared"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    response: Response,
    current_user: CurrentUser,
) -> dict:
    """
    Logout the current user by clearing the JWT cookie.

    **Response 200:** Logout successful. JWT cookie cleared.
    **Response 401:** Not authenticated (no valid cookie).
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return {"message": "Logout successful"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="GET /api/v1/auth/me - Get current user profile",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Get the currently authenticated user's profile.

    **Response 200:** User profile data.
    **Response 401:** Not authenticated (no valid cookie).
    """
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="PATCH /api/v1/auth/me - Update current user profile",
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Not authenticated"},
        409: {"description": "Email already exists"},
        422: {"description": "Validation error"},
    },
)
async def update_me(
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    """
    Update the current user's profile.

    **Request Body:**
    - `email` (str, optional): New email address.
    - `password` (str, optional): New password. 8-100 characters.

    **Response 200:** Profile updated successfully.
    **Response 401:** Not authenticated.
    **Response 409:** Email already exists.
    **Response 422:** Request body validation failed.
    """
    # Check if email is being changed and is unique
    if user_data.email and user_data.email != current_user.email:
        if await AuthService.check_email_exists(db, user_data.email):
            raise ConflictException(
                f"Email '{user_data.email}' is already registered")
        current_user.email = user_data.email

    # Update password if provided
    if user_data.password:
        current_user.hashed_password = AuthService.hash_password(
            user_data.password)

    await db.flush()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="DELETE /api/v1/auth/users/{user_id} - Delete user by ID",
    responses={
        204: {"description": "User deleted successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized to delete this user"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: str,
    current_user: CurrentUser,
    db: DbSession,
    response: Response,
) -> None:
    """
    Delete a user by their ID.

    **Path Parameters:**
    - `user_id` (str): The UUID of the user to delete.

    **Response 204:** User deleted successfully (no content).
    **Response 401:** Not authenticated (no valid cookie).
    **Response 403:** Not authorized (can only delete own account or must be admin).
    **Response 404:** User not found.

    Users can delete their own accounts. Only admins can delete other users' accounts.
    If deleting own account, the JWT cookie will also be cleared.
    """
    from uuid import UUID

    # Convert user_id to UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise BadRequestException("Invalid user ID format")

    # Get the user to delete
    user_to_delete = await AuthService.get_user_by_id(db, user_uuid)
    if not user_to_delete:
        from api.exceptions import NotFoundException
        raise NotFoundException(f"User with ID '{user_id}' not found")

    # Check authorization: users can delete themselves, admins can delete anyone
    from api.models.user import UserRole
    if current_user.id != user_uuid and current_user.role != UserRole.ADMIN:
        from api.exceptions import ForbiddenException
        raise ForbiddenException("You can only delete your own account")

    await AuthService.delete_user(db, user_to_delete)

    # If deleting own account, clear the JWT cookie
    if current_user.id == user_uuid:
        response.delete_cookie(
            key=settings.COOKIE_NAME,
            httponly=True,
            secure=False,
            samesite="lax",
        )
