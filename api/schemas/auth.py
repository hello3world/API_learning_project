"""
Authentication schemas.

This module defines Pydantic schemas for user registration, login, and token handling.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.models.user import UserRole


class UserCreate(BaseModel):
    """
    Schema for user registration.

    **Fields:**
    - `username` (str, required): Unique username. 3-50 characters.
    - `email` (str, required): Valid email address.
    - `password` (str, required): Password. 8-100 characters.
    - `role` (str, optional): User role. Possible values: admin, operator, viewer. Default: "viewer".
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username. 3-50 characters.",
        examples=["john_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address.",
        examples=["john@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password. 8-100 characters.",
        examples=["securepassword123"],
    )
    role: Optional[UserRole] = Field(
        default=UserRole.VIEWER,
        description="User role. One of: admin, operator, viewer. Default: viewer.",
    )


class UserLogin(BaseModel):
    """
    Schema for user login.

    **Fields:**
    - `username` (str, required): Username or email.
    - `password` (str, required): User password.
    """
    username: str = Field(
        ...,
        description="Username or email address.",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        description="User password.",
        examples=["securepassword123"],
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.

    **Fields:**
    - `email` (str, optional): New email address.
    - `password` (str, optional): New password. 8-100 characters.
    """
    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address.",
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=100,
        description="New password. 8-100 characters.",
    )


class UserResponse(BaseModel):
    """
    Schema for user response.

    **Fields:**
    - `id` (UUID): User unique identifier.
    - `username` (str): Username.
    - `email` (str): Email address.
    - `is_active` (bool): Whether user is active.
    - `role` (str): User role.
    - `created_at` (datetime): Account creation timestamp.
    """
    id: UUID = Field(..., description="User unique identifier.")
    username: str = Field(..., description="Username.")
    email: str = Field(..., description="Email address.")
    is_active: bool = Field(...,
                            description="Whether user is active. True or False.")
    role: UserRole = Field(...,
                           description="User role. Possible values: admin, operator, viewer.")
    created_at: datetime = Field(...,
                                 description="Account creation timestamp in ISO 8601 format.")

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    """
    Schema for JWT token data (internal use).

    **Fields:**
    - `user_id` (UUID): User identifier from token.
    - `username` (str): Username from token.
    - `role` (str): User role from token.
    """
    user_id: UUID = Field(..., description="User identifier.")
    username: str = Field(..., description="Username.")
    role: UserRole = Field(..., description="User role.")


class LoginResponse(BaseModel):
    """
    Schema for successful login response.

    **Fields:**
    - `message` (str): Success message.
    - `user` (UserResponse): User details.
    """
    message: str = Field(default="Login successful",
                         description="Success message.")
    user: UserResponse = Field(..., description="User details.")
