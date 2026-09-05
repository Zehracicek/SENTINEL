"""transmission_log: olculen byte metrikleri

Önceki sürüm `bytes_saved` değerini `(total - transmitted) * 256` ile
hesaplıyordu. Bir okuma aslında iki float64 olarak serialize edilir (16 byte),
dolayısıyla tasarruf ~16 kat şişiyor ve toplamda verinin kendi hacminden kat
kat büyük bir "tasarruf" raporlanıyordu.

Artık:
  baseline_bytes    filtresiz + sıkıştırmasız referans hacim
  uplink_bytes      gerçekten iletilen (delta + DEFLATE sonrası) hacim
  bytes_saved       baseline_bytes - uplink_bytes
  compression_ratio uplink_bytes / baseline_bytes  (byte tabanlı)
  packet_ratio      transmitted_packets / total_packets (eski oranın anlamı)

Mevcut satırlar eski/yanlış ölçekte olduğu için byte alanları sıfırlanır;
karışık ölçekli veriyi bir arada tutmak grafikleri bozar.

Revision ID: 007
Revises: 006
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transmission_log",
        sa.Column(
            "baseline_bytes", sa.BigInteger(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "transmission_log",
        sa.Column("uplink_bytes", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "transmission_log",
        sa.Column("packet_ratio", sa.Float(), nullable=False, server_default="1.0"),
    )

    # Eski compression_ratio paket oranıydı; anlamını koruyarak packet_ratio'ya taşı.
    op.execute("UPDATE transmission_log SET packet_ratio = compression_ratio")
    # Uydurma 256 sabitiyle üretilmiş byte değerlerini sıfırla.
    op.execute("UPDATE transmission_log SET bytes_saved = 0, compression_ratio = 1.0")


def downgrade() -> None:
    op.execute("UPDATE transmission_log SET compression_ratio = packet_ratio")
    op.drop_column("transmission_log", "packet_ratio")
    op.drop_column("transmission_log", "uplink_bytes")
    op.drop_column("transmission_log", "baseline_bytes")
