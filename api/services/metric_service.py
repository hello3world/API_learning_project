"""
Metric service.

This module handles business logic for miner metrics operations.
"""

import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.metric import MinerMetric
from api.schemas.metric import MetricCreate


class MetricService:
    """Service for miner metrics operations."""
    
    @staticmethod
    async def get_metrics(
        db: AsyncSession,
        miner_id: UUID,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        page: int = 1,
        size: int = 100,
    ) -> tuple[list[MinerMetric], int]:
        """
        Get paginated list of metrics for a miner.
        
        Args:
            db: Database session.
            miner_id: Parent miner ID.
            from_dt: Optional start datetime filter.
            to_dt: Optional end datetime filter.
            page: Page number (1-indexed).
            size: Page size (max 1000).
            
        Returns:
            Tuple of (metrics list, total count).
        """
        size = min(size, 1000)  # Cap at 1000
        
        query = select(MinerMetric).where(MinerMetric.miner_id == miner_id)
        count_query = select(func.count(MinerMetric.id)).where(
            MinerMetric.miner_id == miner_id
        )
        
        if from_dt:
            query = query.where(MinerMetric.recorded_at >= from_dt)
            count_query = count_query.where(MinerMetric.recorded_at >= from_dt)
        
        if to_dt:
            query = query.where(MinerMetric.recorded_at <= to_dt)
            count_query = count_query.where(MinerMetric.recorded_at <= to_dt)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(
            MinerMetric.recorded_at.desc()
        )
        
        result = await db.execute(query)
        metrics = list(result.scalars().all())
        
        return metrics, total
    
    @staticmethod
    async def get_latest_metric(
        db: AsyncSession,
        miner_id: UUID,
    ) -> Optional[MinerMetric]:
        """
        Get the most recent metric for a miner.
        
        Args:
            db: Database session.
            miner_id: Parent miner ID.
            
        Returns:
            Latest MinerMetric if exists, None otherwise.
        """
        result = await db.execute(
            select(MinerMetric)
            .where(MinerMetric.miner_id == miner_id)
            .order_by(MinerMetric.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_metric(
        db: AsyncSession,
        miner_id: UUID,
        metric_data: MetricCreate,
    ) -> MinerMetric:
        """
        Create a new metric snapshot.
        
        Args:
            db: Database session.
            miner_id: Parent miner ID.
            metric_data: Metric creation data.
            
        Returns:
            Newly created MinerMetric.
        """
        metric = MinerMetric(
            miner_id=miner_id,
            hashrate_th=metric_data.hashrate_th,
            temperature_c=metric_data.temperature_c,
            fan_speed_rpm=metric_data.fan_speed_rpm,
            power_watts=metric_data.power_watts,
            accepted_shares=metric_data.accepted_shares or 0,
            rejected_shares=metric_data.rejected_shares or 0,
            pool_difficulty=metric_data.pool_difficulty,
        )
        
        db.add(metric)
        await db.flush()
        await db.refresh(metric)
        
        return metric
    
    @staticmethod
    async def delete_metrics_by_range(
        db: AsyncSession,
        miner_id: UUID,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
    ) -> int:
        """
        Delete metrics within a date range.
        
        Args:
            db: Database session.
            miner_id: Parent miner ID.
            from_dt: Optional start datetime.
            to_dt: Optional end datetime.
            
        Returns:
            Number of deleted records.
        """
        conditions = [MinerMetric.miner_id == miner_id]
        
        if from_dt:
            conditions.append(MinerMetric.recorded_at >= from_dt)
        
        if to_dt:
            conditions.append(MinerMetric.recorded_at <= to_dt)
        
        result = await db.execute(
            delete(MinerMetric).where(and_(*conditions)).returning(MinerMetric.id)
        )
        
        deleted_ids = result.fetchall()
        await db.flush()
        
        return len(deleted_ids)
    
    @staticmethod
    def calculate_pages(total: int, size: int) -> int:
        """Calculate total number of pages."""
        return math.ceil(total / size) if total > 0 else 0
