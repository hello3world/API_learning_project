"""
User model for authentication and authorization.

This module defines the User ORM model with role-based access control support.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.farm import MiningFarm
    from api.models.alert import Alert


class UserRole(str, PyEnum):
    """
    User roles for role-based access control.
    
    Attributes:
        ADMIN: Full access to all resources and operations.
        OPERATOR: Can create/modify farms, miners, metrics, alerts.
        VIEWER: Read-only access to all resources.
    """
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    """
    User account model.
    
    Attributes:
        id: Unique identifier (UUID).
        username: Unique username (1-50 characters).
        email: Unique email address.
        hashed_password: Bcrypt hashed password.
        is_active: Whether the user account is active.
        role: User role for RBAC (admin, operator, viewer).
        created_at: Account creation timestamp.
    """
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        default=UserRole.VIEWER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    farms: Mapped[list["MiningFarm"]] = relationship(
        "MiningFarm",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    acknowledged_alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="acknowledged_by_user",
        foreign_keys="Alert.acknowledged_by",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
