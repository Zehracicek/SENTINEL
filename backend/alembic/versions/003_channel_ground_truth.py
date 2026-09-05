"""sensor_readings: channel_id, ground_truth_anomaly

Revision ID: 003
Revises: 002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("channel_id", sa.String(20), nullable=False, server_default=""),
    )
    op.add_column(
        "sensor_readings",
        sa.Column(
            "ground_truth_anomaly",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.create_index(
        "ix_sensor_readings_channel_id",
        "sensor_readings",
        ["channel_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_readings_channel_id", table_name="sensor_readings")
    op.drop_column("sensor_readings", "ground_truth_anomaly")
    op.drop_column("sensor_readings", "channel_id")
