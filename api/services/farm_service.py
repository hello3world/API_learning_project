"""
Farm service.

This module handles business logic for mining farm operations.
"""

import math
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models.farm import FarmStatus, MiningFarm
from api.models.miner import Miner, MinerStatus
from api.models.metric import MinerMetric
from api.schemas.farm import FarmCreate, FarmPatch, FarmSummary, FarmUpdate


class FarmService:
    """Service for mining farm operations."""
    
    @staticmethod
    async def get_farms(
        db: AsyncSession,
        owner_id: Optional[UUID] = None,
        status: Optional[FarmStatus] = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[list[MiningFarm], int]:
        """
        Get paginated list of farms.
        
        Args:
            db: Database session.
            owner_id: Optional filter by owner.
            status: Optional filter by status.
            page: Page number (1-indexed).
            size: Page size.
            
        Returns:
            Tuple of (farms list, total count).
        """
        query = select(MiningFarm).options(selectinload(MiningFarm.miners))
        count_query = select(func.count(MiningFarm.id))
        
        if owner_id:
            query = query.where(MiningFarm.owner_id == owner_id)
            count_query = count_query.where(MiningFarm.owner_id == owner_id)
        
        if status:
            query = query.where(MiningFarm.status == status)
            count_query = count_query.where(MiningFarm.status == status)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(MiningFarm.created_at.desc())
        
        result = await db.execute(query)
        farms = list(result.scalars().all())
        
        return farms, total
    
    @staticmethod
    async def get_farm_by_id(
        db: AsyncSession,
        farm_id: UUID,
    ) -> Optional[MiningFarm]:
        """
        Get a farm by ID.
        
        Args:
            db: Database session.
            farm_id: Farm unique identifier.
            
        Returns:
            MiningFarm if found, None otherwise.
        """
        result = await db.execute(
            select(MiningFarm)
            .options(selectinload(MiningFarm.miners))
            .where(MiningFarm.id == farm_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_farm(
        db: AsyncSession,
        farm_data: FarmCreate,
        owner_id: UUID,
    ) -> MiningFarm:
        """
        Create a new mining farm.
        
        Args:
            db: Database session.
            farm_data: Farm creation data.
            owner_id: Owner user ID.
            
        Returns:
            Newly created MiningFarm.
        """
        farm = MiningFarm(
            name=farm_data.name,
            location=farm_data.location,
            total_power_kw=farm_data.total_power_kw,
            status=farm_data.status or FarmStatus.OFFLINE,
            owner_id=owner_id,
        )
        
        db.add(farm)
        await db.flush()
        await db.refresh(farm)
        
        return farm
    
    @staticmethod
    async def update_farm(
        db: AsyncSession,
        farm: MiningFarm,
        farm_data: FarmUpdate,
    ) -> MiningFarm:
        """
        Full update of a farm.
        
        Args:
            db: Database session.
            farm: Existing farm to update.
            farm_data: New farm data.
            
        Returns:
            Updated MiningFarm.
        """
        farm.name = farm_data.name
        farm.location = farm_data.location
        farm.total_power_kw = farm_data.total_power_kw
        farm.status = farm_data.status
        
        await db.flush()
        await db.refresh(farm)
        
        return farm
    
    @staticmethod
    async def patch_farm(
        db: AsyncSession,
        farm: MiningFarm,
        farm_data: FarmPatch,
    ) -> MiningFarm:
        """
        Partial update of a farm.
        
        Args:
            db: Database session.
            farm: Existing farm to update.
            farm_data: Partial farm data.
            
        Returns:
            Updated MiningFarm.
        """
        update_data = farm_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(farm, field, value)
        
        await db.flush()
        await db.refresh(farm)
        
        return farm
    
    @staticmethod
    async def delete_farm(
        db: AsyncSession,
        farm: MiningFarm,
    ) -> None:
        """
        Delete a farm and all related data.
        
        Args:
            db: Database session.
            farm: Farm to delete.
        """
        await db.delete(farm)
        await db.flush()
    
    @staticmethod
    async def get_farm_summary(
        db: AsyncSession,
        farm_id: UUID,
    ) -> Optional[FarmSummary]:
        """
        Get aggregated statistics for a farm.
        
        Args:
            db: Database session.
            farm_id: Farm unique identifier.
            
        Returns:
            FarmSummary with aggregated stats or None if farm not found.
        """
        # Check farm exists
        farm_result = await db.execute(
            select(MiningFarm.id).where(MiningFarm.id == farm_id)
        )
        if farm_result.scalar_one_or_none() is None:
            return None
        
        # Get miner counts
        total_miners_result = await db.execute(
            select(func.count(Miner.id)).where(Miner.farm_id == farm_id)
        )
        total_miners = total_miners_result.scalar() or 0
        
        active_miners_result = await db.execute(
            select(func.count(Miner.id)).where(
                Miner.farm_id == farm_id,
                Miner.status == MinerStatus.ACTIVE,
            )
        )
        active_miners = active_miners_result.scalar() or 0
        
        # Get latest metrics for active miners - using subquery for latest metric per miner
        from sqlalchemy import and_
        
        # Subquery to get the latest metric timestamp for each miner
        latest_metric_subq = (
            select(
                MinerMetric.miner_id,
                func.max(MinerMetric.recorded_at).label("max_recorded_at")
            )
            .join(Miner, Miner.id == MinerMetric.miner_id)
            .where(Miner.farm_id == farm_id)
            .group_by(MinerMetric.miner_id)
            .subquery()
        )
        
        # Query to get the sum of metrics from latest records
        metrics_result = await db.execute(
            select(
                func.coalesce(func.sum(MinerMetric.hashrate_th), 0).label("total_hashrate"),
                func.coalesce(func.sum(MinerMetric.power_watts), 0).label("total_power"),
                func.coalesce(func.avg(MinerMetric.temperature_c), 0).label("avg_temp"),
            )
            .join(
                latest_metric_subq,
                and_(
                    MinerMetric.miner_id == latest_metric_subq.c.miner_id,
                    MinerMetric.recorded_at == latest_metric_subq.c.max_recorded_at,
                )
            )
        )
        
        row = metrics_result.one()
        
        return FarmSummary(
            farm_id=farm_id,
            total_hashrate_th=float(row.total_hashrate or 0),
            active_miners=active_miners,
            total_miners=total_miners,
            total_power_watts=float(row.total_power or 0),
            avg_temperature_c=float(row.avg_temp or 0),
        )
    
    @staticmethod
    def calculate_pages(total: int, size: int) -> int:
        """Calculate total number of pages."""
        return math.ceil(total / size) if total > 0 else 0
