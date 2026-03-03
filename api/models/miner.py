"""
Miner model.

This module defines the Miner ORM model representing a mining hardware unit (ASIC).
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.farm import MiningFarm
    from api.models.metric import MinerMetric
    from api.models.alert import Alert


class MinerStatus(str, PyEnum):
    """
    Miner operational status.
    
    Attributes:
        ACTIVE: Miner is running and hashing.
        INACTIVE: Miner is not running.
        ERROR: Miner has encountered an error.
        MAINTENANCE: Miner is under maintenance.
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Miner(Base):
    """
    Miner model representing a mining hardware unit (ASIC).
    
    Attributes:
        id: Unique identifier (UUID).
        farm_id: Reference to the parent mining farm.
        name: Miner display name (1-100 characters).
        model: Hardware model (e.g., "Antminer S19 Pro").
        ip_address: Network IP address (optional, IPv4/IPv6).
        mac_address: Network MAC address (optional).
        status: Operational status (active, inactive, error, maintenance).
        worker_name: Pool worker identifier (optional).
        created_at: Miner registration timestamp.
        updated_at: Last update timestamp.
    """
    __tablename__ = "miners"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mining_farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    mac_address: Mapped[str | None] = mapped_column(
        String(17),  # XX:XX:XX:XX:XX:XX format
        nullable=True,
    )
    status: Mapped[MinerStatus] = mapped_column(
        Enum(MinerStatus, name="miner_status", values_callable=lambda x: [e.value for e in x]),
        default=MinerStatus.INACTIVE,
        nullable=False,
    )
    worker_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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
    farm: Mapped["MiningFarm"] = relationship(
        "MiningFarm",
        back_populates="miners",
    )
    metrics: Mapped[list["MinerMetric"]] = relationship(
        "MinerMetric",
        back_populates="miner",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="miner",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Miner(id={self.id}, name={self.name}, model={self.model}, status={self.status})>"
