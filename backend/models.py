import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_type = Column(String(10), nullable=False, index=True)
    channel_id = Column(String(20), nullable=False, default="", index=True)
    raw_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    ground_truth_anomaly = Column(Boolean, nullable=False, default=False)
    is_transmitted = Column(Boolean, nullable=False, default=False)
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    sol = Column(Integer, nullable=False, default=1)
    is_novel = Column(Boolean, nullable=False, default=False)
    replay_index = Column(Integer, nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    anomaly_events = relationship(
        "AnomalyEvent", back_populates="reading", cascade="all, delete-orphan"
    )
    uplink_queue_items = relationship(
        "UplinkQueueItem", back_populates="reading", cascade="all, delete-orphan"
    )
    orbiter_queue_items = relationship(
        "OrbiterQueueItem", back_populates="reading", cascade="all, delete-orphan"
    )


class UplinkQueueItem(Base):
    """DSN uplink: yüksek skorlu paketler önce kuyruğa alınır, bant sınırıyla sırayla iletilir."""

    __tablename__ = "uplink_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reading_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sensor_readings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    uplink_priority = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    queued_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
    dsn_station = Column(String(50), nullable=True)

    reading = relationship("SensorReading", back_populates="uplink_queue_items")


class OrbiterQueueItem(Base):
    __tablename__ = "orbiter_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reading_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sensor_readings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status = Column(String(20), nullable=False, default="pending", index=True)
    queued_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    forwarded_at = Column(DateTime(timezone=True), nullable=True)

    reading = relationship("SensorReading", back_populates="orbiter_queue_items")


class OrbiterRelayLog(Base):
    __tablename__ = "orbiter_relay_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    packets_received = Column(Integer, nullable=False)
    packets_forwarded = Column(Integer, nullable=False)
    relay_latency_ms = Column(Float, nullable=False)
    pass_id = Column(String(50), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ModelUpdate(Base):
    __tablename__ = "model_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(Integer, nullable=False)
    threshold_suggestion = Column(Float, nullable=False)
    federated_round = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reading_id = Column(
        UUID(as_uuid=True), ForeignKey("sensor_readings.id"), nullable=False
    )
    anomaly_type = Column(String(30), nullable=False, index=True)
    severity = Column(String(10), nullable=False)
    description = Column(Text, nullable=False)
    scientific_priority = Column(Integer, nullable=False)
    acknowledged = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    reading = relationship("SensorReading", back_populates="anomaly_events")


class TransmissionLog(Base):
    __tablename__ = "transmission_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    total_packets = Column(Integer, nullable=False)
    transmitted_packets = Column(Integer, nullable=False)
    # Filtresiz + sıkıştırmasız referans hacim ve gerçekten iletilen hacim
    baseline_bytes = Column(BigInteger, nullable=False, default=0)
    uplink_bytes = Column(BigInteger, nullable=False, default=0)
    bytes_saved = Column(BigInteger, nullable=False, default=0)
    # Byte tabanlı: uplink_bytes / baseline_bytes (düşük = iyi)
    compression_ratio = Column(Float, nullable=False, default=1.0)
    # Paket sayısı tabanlı: transmitted_packets / total_packets
    packet_ratio = Column(Float, nullable=False, default=1.0)
    transmission_window = Column(String(50), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
