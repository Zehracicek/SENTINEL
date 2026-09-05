"""uplink_queue table

Revision ID: 002
Revises: 001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uplink_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("reading_id", UUID(as_uuid=True), nullable=False),
        sa.Column("uplink_priority", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dsn_station", sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(["reading_id"], ["sensor_readings.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("reading_id", name="uq_uplink_queue_reading_id"),
    )
    op.create_index("ix_uplink_queue_status", "uplink_queue", ["status"])


def downgrade() -> None:
    op.drop_index("ix_uplink_queue_status", table_name="uplink_queue")
    op.drop_table("uplink_queue")
