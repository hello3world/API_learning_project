"""
Authentication service.

This module handles user authentication, JWT token creation/validation,
and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
import jwt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.models.user import User, UserRole
from api.schemas.auth import TokenData, UserCreate


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password.

        Returns:
            Hashed password string.
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify.
            hashed_password: Stored password hash.

        Returns:
            True if password matches, False otherwise.
        """
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def create_access_token(
        user_id: UUID,
        username: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: User's unique identifier.
            username: User's username.
            role: User's role.
            expires_delta: Optional custom expiration time.

        Returns:
            Encoded JWT token string.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string.

        Returns:
            TokenData if valid, None if invalid or expired.
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id = payload.get("sub")
            username = payload.get("username")
            role = payload.get("role")

            if user_id is None or username is None or role is None:
                return None

            return TokenData(
                user_id=UUID(user_id),
                username=username,
                role=UserRole(role),
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    async def get_user_by_username(
        db: AsyncSession,
        username: str,
    ) -> Optional[User]:
        """
        Get a user by username or email.

        Args:
            db: Database session.
            username: Username or email to search.

        Returns:
            User if found, None otherwise.
        """
        result = await db.execute(
            select(User).where(
                or_(User.username == username, User.email == username)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            db: Database session.
            user_id: User's unique identifier.

        Returns:
            User if found, None otherwise.
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: UserCreate,
    ) -> User:
        """
        Create a new user.

        Args:
            db: Database session.
            user_data: User registration data.

        Returns:
            Newly created User.
        """
        hashed_password = AuthService.hash_password(user_data.password)

        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role or UserRole.VIEWER,
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)

        return user

    @staticmethod
    async def check_username_exists(
        db: AsyncSession,
        username: str,
    ) -> bool:
        """
        Check if a username already exists.

        Args:
            db: Database session.
            username: Username to check.

        Returns:
            True if exists, False otherwise.
        """
        result = await db.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def check_email_exists(
        db: AsyncSession,
        email: str,
    ) -> bool:
        """
        Check if an email already exists.

        Args:
            db: Database session.
            email: Email to check.

        Returns:
            True if exists, False otherwise.
        """
        result = await db.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate a user by username/email and password.

        Args:
            db: Database session.
            username: Username or email.
            password: Plain text password.

        Returns:
            User if authentication successful, None otherwise.
        """
        user = await AuthService.get_user_by_username(db, username)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            return None

        return user

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user: User,
    ) -> None:
        """
        Delete a user from the database.

        Args:
            db: Database session.
            user: User to delete.
        """
        await db.delete(user)
        await db.flush()
