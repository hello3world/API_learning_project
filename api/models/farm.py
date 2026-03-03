"""
Mining Farm model.

This module defines the MiningFarm ORM model representing a physical mining facility.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.user import User
    from api.models.miner import Miner
    from api.models.alert import Alert


class FarmStatus(str, PyEnum):
    """
    Mining farm operational status.
    
    Attributes:
        ONLINE: Farm is fully operational.
        OFFLINE: Farm is not operating.
        MAINTENANCE: Farm is under maintenance.
    """
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class MiningFarm(Base):
    """
    Mining farm model representing a physical mining facility.
    
    Attributes:
        id: Unique identifier (UUID).
        name: Farm display name (1-100 characters).
        location: Physical location description (optional).
        owner_id: Reference to the owning user.
        total_power_kw: Total available power in kilowatts (optional).
        status: Operational status (online, offline, maintenance).
        created_at: Farm creation timestamp.
        updated_at: Last update timestamp.
    """
    __tablename__ = "mining_farms"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_power_kw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus, name="farm_status", values_callable=lambda x: [e.value for e in x]),
        default=FarmStatus.OFFLINE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="farms",
    )
    miners: Mapped[list["Miner"]] = relationship(
        "Miner",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<MiningFarm(id={self.id}, name={self.name}, status={self.status})>"
