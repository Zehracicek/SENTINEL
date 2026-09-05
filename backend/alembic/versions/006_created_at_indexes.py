"""created_at indeksleri

crud.py'deki sorguların neredeyse tamamı `ORDER BY created_at DESC ... LIMIT n`
biçiminde. Simülasyon 12 kanalı sürekli yazdığı için tablolar hızla büyür ve
indeks olmadan her sorgu sequential scan'e döner.

sensor_readings üzerinde ek olarak (sensor_type, created_at) bileşik indeksi
var; `/api/sensor-data?sensor_type=TEMP` filtresi bunu kullanır.

Revision ID: 006
Revises: 005
"""
from typing import Sequence, Union

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_sensor_readings_created_at",
        "sensor_readings",
        ["created_at"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_sensor_readings_sensor_type_created_at",
        "sensor_readings",
        ["sensor_type", "created_at"],
    )
    op.create_index(
        "ix_anomaly_events_created_at",
        "anomaly_events",
        ["created_at"],
    )
    op.create_index(
        "ix_transmission_log_created_at",
        "transmission_log",
        ["created_at"],
    )
    op.create_index(
        "ix_orbiter_relay_log_created_at",
        "orbiter_relay_log",
        ["created_at"],
    )
    op.create_index(
        "ix_model_updates_created_at",
        "model_updates",
        ["created_at"],
    )
    # drain_uplink_queue: WHERE status='pending' ORDER BY uplink_priority DESC, queued_at
    op.create_index(
        "ix_uplink_queue_status_priority",
        "uplink_queue",
        ["status", "uplink_priority", "queued_at"],
    )
    # process_orbiter_drain: WHERE status='pending' ORDER BY queued_at
    op.create_index(
        "ix_orbiter_queue_status_queued_at",
        "orbiter_queue",
        ["status", "queued_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_orbiter_queue_status_queued_at", table_name="orbiter_queue")
    op.drop_index("ix_uplink_queue_status_priority", table_name="uplink_queue")
    op.drop_index("ix_model_updates_created_at", table_name="model_updates")
    op.drop_index("ix_orbiter_relay_log_created_at", table_name="orbiter_relay_log")
    op.drop_index("ix_transmission_log_created_at", table_name="transmission_log")
    op.drop_index("ix_anomaly_events_created_at", table_name="anomaly_events")
    op.drop_index(
        "ix_sensor_readings_sensor_type_created_at", table_name="sensor_readings"
    )
    op.drop_index("ix_sensor_readings_created_at", table_name="sensor_readings")
