"""sensor_readings.replay_index — dizi-seviyesi değerlendirme

Replay imleci (`simulator` `_idx`) daha önce yalnızca bellek içiydi.
Hundman örtüşme metriği kanal + indeks ister; eski satırlar NULL kalır
ve sequence değerlendirmesinden çıkar.

Revision ID: 008
Revises: 007
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("replay_index", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_sensor_readings_replay_index",
        "sensor_readings",
        ["replay_index"],
    )
    op.create_index(
        "ix_sensor_readings_channel_replay",
        "sensor_readings",
        ["channel_id", "replay_index"],
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_readings_channel_replay", table_name="sensor_readings")
    op.drop_index("ix_sensor_readings_replay_index", table_name="sensor_readings")
    op.drop_column("sensor_readings", "replay_index")
