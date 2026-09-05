from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SensorReadingCreate(BaseModel):
    sensor_type: str
    channel_id: str = ""
    raw_value: float
    unit: str
    anomaly_score: float = 0.0
    is_anomaly: bool = False
    ground_truth_anomaly: bool = False
    is_transmitted: bool = False
    is_novel: bool = False
    replay_index: Optional[int] = None
    location_lat: float
    location_lon: float
    sol: int = 1


class SensorReadingResponse(BaseModel):
    id: UUID
    sensor_type: str
    channel_id: str
    raw_value: float
    unit: str
    anomaly_score: float
    is_anomaly: bool
    ground_truth_anomaly: bool
    is_transmitted: bool
    is_novel: bool = False
    replay_index: Optional[int] = None
    location_lat: float
    location_lon: float
    sol: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SensorStats(BaseModel):
    sensor_type: str
    count: int
    mean: float
    std: float
    anomaly_rate: float


class AnomalyEventCreate(BaseModel):
    reading_id: UUID
    anomaly_type: str
    severity: str
    description: str
    scientific_priority: int = Field(ge=1, le=10)


class AnomalyEventResponse(BaseModel):
    id: UUID
    reading_id: UUID
    anomaly_type: str
    severity: str
    description: str
    scientific_priority: int
    acknowledged: bool
    created_at: datetime
    # İlişkili okumadan gelir; istemci açıklama metnini ayrıştırmak zorunda kalmasın
    sensor_type: Optional[str] = None
    channel_id: Optional[str] = None

    model_config = {"from_attributes": True}


class AnomalyAcknowledge(BaseModel):
    acknowledged: bool = True


class AnomalyStats(BaseModel):
    anomaly_type: str
    count: int
    avg_priority: float


class AnomalyEventDetailResponse(AnomalyEventResponse):
    reading: Optional[SensorReadingResponse] = None


class TransmissionLogResponse(BaseModel):
    id: UUID
    batch_id: UUID
    total_packets: int
    transmitted_packets: int
    baseline_bytes: int = 0
    uplink_bytes: int = 0
    bytes_saved: int
    compression_ratio: float
    packet_ratio: float = 1.0
    transmission_window: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=500)


class OverviewStats(BaseModel):
    """crud.get_overview_stats çıktısının şekli (WebSocket stats_update içinde)."""

    total_readings: int
    transmitted_readings: int = 0
    total_anomalies: int
    # Ölçülen byte'lara dayanır: 1 - uplink_bytes / baseline_bytes
    bandwidth_saved_percent: float
    highest_severity: Optional[str] = None
    total_bytes_saved: int = 0
    baseline_bytes: int = 0
    uplink_bytes: int = 0
    packet_ratio: float = 0.0


class OrbiterRelayLogResponse(BaseModel):
    id: UUID
    batch_id: UUID
    packets_received: int
    packets_forwarded: int
    relay_latency_ms: float
    pass_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ModelUpdateResponse(BaseModel):
    id: UUID
    model_version: int
    threshold_suggestion: float
    federated_round: int
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
