"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sensor_readings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("sensor_type", sa.String(10), nullable=False, index=True),
        sa.Column("raw_value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("anomaly_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("is_anomaly", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_transmitted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("location_lat", sa.Float, nullable=False),
        sa.Column("location_lon", sa.Float, nullable=False),
        sa.Column("sol", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "anomaly_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "reading_id",
            UUID(as_uuid=True),
            sa.ForeignKey("sensor_readings.id"),
            nullable=False,
        ),
        sa.Column("anomaly_type", sa.String(30), nullable=False, index=True),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("scientific_priority", sa.Integer, nullable=False),
        sa.Column("acknowledged", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "transmission_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", UUID(as_uuid=True), nullable=False),
        sa.Column("total_packets", sa.Integer, nullable=False),
        sa.Column("transmitted_packets", sa.Integer, nullable=False),
        sa.Column("bytes_saved", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("compression_ratio", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("transmission_window", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("transmission_log")
    op.drop_table("anomaly_events")
    op.drop_table("sensor_readings")
