"""Initial schema with all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    user_role = postgresql.ENUM('admin', 'operator', 'viewer', name='user_role', create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)
    
    farm_status = postgresql.ENUM('online', 'offline', 'maintenance', name='farm_status', create_type=False)
    farm_status.create(op.get_bind(), checkfirst=True)
    
    miner_status = postgresql.ENUM('active', 'inactive', 'error', 'maintenance', name='miner_status', create_type=False)
    miner_status.create(op.get_bind(), checkfirst=True)
    
    alert_severity = postgresql.ENUM('info', 'warning', 'critical', name='alert_severity', create_type=False)
    alert_severity.create(op.get_bind(), checkfirst=True)
    
    alert_type = postgresql.ENUM('high_temp', 'low_hashrate', 'offline', 'power_spike', 'custom', name='alert_type', create_type=False)
    alert_type.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('role', user_role, default='viewer', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create mining_farms table
    op.create_table(
        'mining_farms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('total_power_kw', sa.Float(), nullable=True),
        sa.Column('status', farm_status, default='offline', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create miners table
    op.create_table(
        'miners',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mining_farms.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('mac_address', sa.String(17), nullable=True),
        sa.Column('status', miner_status, default='inactive', nullable=False),
        sa.Column('worker_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create miner_metrics table
    op.create_table(
        'miner_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('miner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('miners.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('hashrate_th', sa.Float(), nullable=False),
        sa.Column('temperature_c', sa.Float(), nullable=False),
        sa.Column('fan_speed_rpm', sa.Integer(), nullable=True),
        sa.Column('power_watts', sa.Float(), nullable=False),
        sa.Column('accepted_shares', sa.Integer(), default=0, nullable=False),
        sa.Column('rejected_shares', sa.Integer(), default=0, nullable=False),
        sa.Column('pool_difficulty', sa.Float(), nullable=True),
    )
    
    # Create composite index for time-series queries
    op.create_index(
        'ix_miner_metrics_miner_recorded',
        'miner_metrics',
        ['miner_id', 'recorded_at'],
    )
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('miner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('miners.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mining_farms.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('severity', alert_severity, default='info', nullable=False),
        sa.Column('alert_type', alert_type, default='custom', nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), default=False, nullable=False),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_index('ix_miner_metrics_miner_recorded')
    op.drop_table('miner_metrics')
    op.drop_table('miners')
    op.drop_table('mining_farms')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS alert_type')
    op.execute('DROP TYPE IF EXISTS alert_severity')
    op.execute('DROP TYPE IF EXISTS miner_status')
    op.execute('DROP TYPE IF EXISTS farm_status')
    op.execute('DROP TYPE IF EXISTS user_role')
