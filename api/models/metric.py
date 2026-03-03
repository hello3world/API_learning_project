"""
Miner Metric model.

This module defines the MinerMetric ORM model for storing mining performance metrics.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.miner import Miner


class MinerMetric(Base):
    """
    Miner performance metric snapshot.
    
    Attributes:
        id: Unique identifier (UUID).
        miner_id: Reference to the miner.
        recorded_at: When the metric was recorded.
        hashrate_th: Hashrate in Terahash/second.
        temperature_c: Temperature in Celsius.
        fan_speed_rpm: Fan speed in RPM (optional).
        power_watts: Power consumption in Watts.
        accepted_shares: Number of accepted shares.
        rejected_shares: Number of rejected shares.
        pool_difficulty: Current pool difficulty (optional).
    """
    __tablename__ = "miner_metrics"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    miner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("miners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    hashrate_th: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    temperature_c: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    fan_speed_rpm: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    power_watts: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    accepted_shares: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    rejected_shares: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    pool_difficulty: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    
    # Relationships
    miner: Mapped["Miner"] = relationship(
        "Miner",
        back_populates="metrics",
    )
    
    # Index for efficient time-series queries
    __table_args__ = (
        Index("ix_miner_metrics_miner_recorded", "miner_id", "recorded_at"),
    )
    
    def __repr__(self) -> str:
        return f"<MinerMetric(id={self.id}, miner_id={self.miner_id}, hashrate={self.hashrate_th} TH/s)>"
