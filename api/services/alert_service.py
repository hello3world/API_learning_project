"""
Alert service.

This module handles business logic for alert operations.
"""

import math
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.alert import Alert, AlertSeverity, AlertType
from api.schemas.alert import AlertCreate


class AlertService:
    """Service for alert operations."""
    
    @staticmethod
    async def get_alerts(
        db: AsyncSession,
        farm_id: Optional[UUID] = None,
        miner_id: Optional[UUID] = None,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        is_acknowledged: Optional[bool] = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[Alert], int]:
        """
        Get paginated list of alerts with filters.
        
        Args:
            db: Database session.
            farm_id: Optional filter by farm.
            miner_id: Optional filter by miner.
            severity: Optional filter by severity.
            alert_type: Optional filter by alert type.
            is_acknowledged: Optional filter by acknowledgment status.
            page: Page number (1-indexed).
            size: Page size.
            
        Returns:
            Tuple of (alerts list, total count).
        """
        query = select(Alert)
        count_query = select(func.count(Alert.id))
        
        if farm_id:
            query = query.where(Alert.farm_id == farm_id)
            count_query = count_query.where(Alert.farm_id == farm_id)
        
        if miner_id:
            query = query.where(Alert.miner_id == miner_id)
            count_query = count_query.where(Alert.miner_id == miner_id)
        
        if severity:
            query = query.where(Alert.severity == severity)
            count_query = count_query.where(Alert.severity == severity)
        
        if alert_type:
            query = query.where(Alert.alert_type == alert_type)
            count_query = count_query.where(Alert.alert_type == alert_type)
        
        if is_acknowledged is not None:
            query = query.where(Alert.is_acknowledged == is_acknowledged)
            count_query = count_query.where(Alert.is_acknowledged == is_acknowledged)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Alert.created_at.desc())
        
        result = await db.execute(query)
        alerts = list(result.scalars().all())
        
        return alerts, total
    
    @staticmethod
    async def get_alert_by_id(
        db: AsyncSession,
        alert_id: UUID,
    ) -> Optional[Alert]:
        """
        Get an alert by ID.
        
        Args:
            db: Database session.
            alert_id: Alert unique identifier.
            
        Returns:
            Alert if found, None otherwise.
        """
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_alert(
        db: AsyncSession,
        alert_data: AlertCreate,
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            db: Database session.
            alert_data: Alert creation data.
            
        Returns:
            Newly created Alert.
        """
        alert = Alert(
            farm_id=alert_data.farm_id,
            miner_id=alert_data.miner_id,
            severity=alert_data.severity or AlertSeverity.INFO,
            alert_type=alert_data.alert_type or AlertType.CUSTOM,
            message=alert_data.message,
        )
        
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        
        return alert
    
    @staticmethod
    async def acknowledge_alert(
        db: AsyncSession,
        alert: Alert,
        user_id: UUID,
    ) -> Alert:
        """
        Mark an alert as acknowledged.
        
        Args:
            db: Database session.
            alert: Alert to acknowledge.
            user_id: ID of the user acknowledging the alert.
            
        Returns:
            Updated Alert.
        """
        alert.is_acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        
        await db.flush()
        await db.refresh(alert)
        
        return alert
    
    @staticmethod
    async def delete_alert(
        db: AsyncSession,
        alert: Alert,
    ) -> None:
        """
        Delete an alert.
        
        Args:
            db: Database session.
            alert: Alert to delete.
        """
        await db.delete(alert)
        await db.flush()
    
    @staticmethod
    def calculate_pages(total: int, size: int) -> int:
        """Calculate total number of pages."""
        return math.ceil(total / size) if total > 0 else 0
