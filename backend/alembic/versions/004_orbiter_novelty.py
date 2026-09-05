"""is_novel, orbiter_queue, orbiter_relay_log

Revision ID: 004
Revises: 003
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("is_novel", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_table(
        "orbiter_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("reading_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("forwarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["reading_id"], ["sensor_readings.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("reading_id", name="uq_orbiter_queue_reading_id"),
    )
    op.create_index("ix_orbiter_queue_status", "orbiter_queue", ["status"])
    op.create_table(
        "orbiter_relay_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", UUID(as_uuid=True), nullable=False),
        sa.Column("packets_received", sa.Integer(), nullable=False),
        sa.Column("packets_forwarded", sa.Integer(), nullable=False),
        sa.Column("relay_latency_ms", sa.Float(), nullable=False),
        sa.Column("pass_id", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("orbiter_relay_log")
    op.drop_index("ix_orbiter_queue_status", table_name="orbiter_queue")
    op.drop_table("orbiter_queue")
    op.drop_column("sensor_readings", "is_novel")
