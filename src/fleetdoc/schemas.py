from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IncidentType(StrEnum):
    THERMAL_THROTTLING = "thermal_throttling"
    ECC_MEMORY_ERROR = "ecc_memory_error"
    NETWORK_FAILURE = "network_failure"
    SENSOR_ANOMALY = "sensor_anomaly"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Incident(StrictModel):
    incident_id: str
    incident_type: IncidentType
    affected_resource: str = Field(description="Canonical node or GPU resource identifier")
    observed_at: str
    summary: str


class GpuTelemetry(StrictModel):
    timestamp: str
    node_id: str
    gpu_id: str
    temperature_c: float
    utilization_pct: float
    power_watts: float
    clock_mhz: int
    ecc_correctable_errors: int
    ecc_uncorrectable_errors: int
    pcie_replay_errors: int


class NodeHealth(StrictModel):
    node_id: str
    observed_at: str
    status: Literal["healthy", "degraded", "unhealthy"]
    cpu_utilization_pct: float
    memory_utilization_pct: float
    network_link_up: bool
    network_packet_loss_pct: float
    network_latency_ms: float
    cooling_fan_rpm: int
    kernel_messages: list[str]


class HistoricalIncident(StrictModel):
    incident_id: str
    observed_at: str
    incident_type: IncidentType
    affected_resource: str
    resolution: str


class TelemetryRequest(StrictModel):
    resource_id: str


class TelemetryResponse(StrictModel):
    resource_id: str
    samples: list[GpuTelemetry]


class NodeHealthRequest(StrictModel):
    node_id: str


class NodeHealthResponse(StrictModel):
    node: NodeHealth


class RecentIncidentsRequest(StrictModel):
    resource_id: str
    limit: int = Field(default=5, ge=1, le=10)


class RecentIncidentsResponse(StrictModel):
    resource_id: str
    incidents: list[HistoricalIncident]


class Evidence(StrictModel):
    source_tool: Literal["get_telemetry", "get_node_health", "get_recent_incidents"]
    observation: str = Field(min_length=1, max_length=500)
    decisive: bool = Field(description="Whether this observation materially determined the diagnosis")


class Diagnosis(StrictModel):
    incident_type: IncidentType
    affected_resource: str
    evidence: list[Evidence] = Field(min_length=1)
    probable_root_cause: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)
    recommended_action: str = Field(min_length=1, max_length=500)
    escalation_required: bool
