"""
Miner service.

This module handles business logic for miner operations.
"""

import math
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.miner import Miner, MinerStatus
from api.schemas.miner import MinerCreate, MinerPatch, MinerUpdate


class MinerService:
    """Service for miner operations."""
    
    @staticmethod
    async def get_miners(
        db: AsyncSession,
        farm_id: UUID,
        status: Optional[MinerStatus] = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[list[Miner], int]:
        """
        Get paginated list of miners for a farm.
        
        Args:
            db: Database session.
            farm_id: Parent farm ID.
            status: Optional filter by status.
            page: Page number (1-indexed).
            size: Page size.
            
        Returns:
            Tuple of (miners list, total count).
        """
        query = select(Miner).where(Miner.farm_id == farm_id)
        count_query = select(func.count(Miner.id)).where(Miner.farm_id == farm_id)
        
        if status:
            query = query.where(Miner.status == status)
            count_query = count_query.where(Miner.status == status)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Miner.created_at.desc())
        
        result = await db.execute(query)
        miners = list(result.scalars().all())
        
        return miners, total
    
    @staticmethod
    async def get_miner_by_id(
        db: AsyncSession,
        miner_id: UUID,
        farm_id: Optional[UUID] = None,
    ) -> Optional[Miner]:
        """
        Get a miner by ID.
        
        Args:
            db: Database session.
            miner_id: Miner unique identifier.
            farm_id: Optional farm ID to validate ownership.
            
        Returns:
            Miner if found, None otherwise.
        """
        query = select(Miner).where(Miner.id == miner_id)
        
        if farm_id:
            query = query.where(Miner.farm_id == farm_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_miner(
        db: AsyncSession,
        farm_id: UUID,
        miner_data: MinerCreate,
    ) -> Miner:
        """
        Create a new miner.
        
        Args:
            db: Database session.
            farm_id: Parent farm ID.
            miner_data: Miner creation data.
            
        Returns:
            Newly created Miner.
        """
        miner = Miner(
            farm_id=farm_id,
            name=miner_data.name,
            model=miner_data.model,
            ip_address=miner_data.ip_address,
            mac_address=miner_data.mac_address,
            status=miner_data.status or MinerStatus.INACTIVE,
            worker_name=miner_data.worker_name,
        )
        
        db.add(miner)
        await db.flush()
        await db.refresh(miner)
        
        return miner
    
    @staticmethod
    async def update_miner(
        db: AsyncSession,
        miner: Miner,
        miner_data: MinerUpdate,
    ) -> Miner:
        """
        Full update of a miner.
        
        Args:
            db: Database session.
            miner: Existing miner to update.
            miner_data: New miner data.
            
        Returns:
            Updated Miner.
        """
        miner.name = miner_data.name
        miner.model = miner_data.model
        miner.ip_address = miner_data.ip_address
        miner.mac_address = miner_data.mac_address
        miner.status = miner_data.status
        miner.worker_name = miner_data.worker_name
        
        await db.flush()
        await db.refresh(miner)
        
        return miner
    
    @staticmethod
    async def patch_miner(
        db: AsyncSession,
        miner: Miner,
        miner_data: MinerPatch,
    ) -> Miner:
        """
        Partial update of a miner.
        
        Args:
            db: Database session.
            miner: Existing miner to update.
            miner_data: Partial miner data.
            
        Returns:
            Updated Miner.
        """
        update_data = miner_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(miner, field, value)
        
        await db.flush()
        await db.refresh(miner)
        
        return miner
    
    @staticmethod
    async def delete_miner(
        db: AsyncSession,
        miner: Miner,
    ) -> None:
        """
        Delete a miner and all related data.
        
        Args:
            db: Database session.
            miner: Miner to delete.
        """
        await db.delete(miner)
        await db.flush()
    
    @staticmethod
    async def check_ip_exists(
        db: AsyncSession,
        farm_id: UUID,
        ip_address: str,
        exclude_miner_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check if an IP address already exists in the farm.
        
        Args:
            db: Database session.
            farm_id: Farm ID to check within.
            ip_address: IP address to check.
            exclude_miner_id: Optional miner ID to exclude (for updates).
            
        Returns:
            True if exists, False otherwise.
        """
        query = select(Miner.id).where(
            Miner.farm_id == farm_id,
            Miner.ip_address == ip_address,
        )
        
        if exclude_miner_id:
            query = query.where(Miner.id != exclude_miner_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    @staticmethod
    def calculate_pages(total: int, size: int) -> int:
        """Calculate total number of pages."""
        return math.ceil(total / size) if total > 0 else 0
