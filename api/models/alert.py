"""
Alert model.

This module defines the Alert ORM model for system alerts and notifications.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.farm import MiningFarm
    from api.models.miner import Miner
    from api.models.user import User


class AlertSeverity(str, PyEnum):
    """
    Alert severity levels.
    
    Attributes:
        INFO: Informational message.
        WARNING: Warning that requires attention.
        CRITICAL: Critical issue requiring immediate action.
    """
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, PyEnum):
    """
    Alert types categorizing the nature of the alert.
    
    Attributes:
        HIGH_TEMP: Temperature exceeds safe threshold.
        LOW_HASHRATE: Hashrate dropped below expected level.
        OFFLINE: Miner or farm went offline.
        POWER_SPIKE: Unusual power consumption detected.
        CUSTOM: User-defined custom alert.
    """
    HIGH_TEMP = "high_temp"
    LOW_HASHRATE = "low_hashrate"
    OFFLINE = "offline"
    POWER_SPIKE = "power_spike"
    CUSTOM = "custom"


class Alert(Base):
    """
    System alert model for notifications and warnings.
    
    Attributes:
        id: Unique identifier (UUID).
        miner_id: Reference to specific miner (optional, for miner-level alerts).
        farm_id: Reference to the mining farm.
        severity: Alert severity level (info, warning, critical).
        alert_type: Type of alert (high_temp, low_hashrate, offline, power_spike, custom).
        message: Human-readable alert message.
        is_acknowledged: Whether the alert has been acknowledged.
        acknowledged_by: Reference to user who acknowledged (optional).
        acknowledged_at: When the alert was acknowledged (optional).
        created_at: Alert creation timestamp.
    """
    __tablename__ = "alerts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    miner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("miners.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mining_farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity", values_callable=lambda x: [e.value for e in x]),
        default=AlertSeverity.INFO,
        nullable=False,
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type", values_callable=lambda x: [e.value for e in x]),
        default=AlertType.CUSTOM,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    miner: Mapped["Miner | None"] = relationship(
        "Miner",
        back_populates="alerts",
    )
    farm: Mapped["MiningFarm"] = relationship(
        "MiningFarm",
        back_populates="alerts",
    )
    acknowledged_by_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="acknowledged_alerts",
        foreign_keys=[acknowledged_by],
    )
    
    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, severity={self.severity}, type={self.alert_type})>"
