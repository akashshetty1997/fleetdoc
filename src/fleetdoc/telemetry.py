from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .schemas import GpuTelemetry, HistoricalIncident, Incident, IncidentType, NodeHealth


@dataclass(frozen=True)
class FleetDataset:
    incidents: dict[str, Incident]
    telemetry: dict[str, list[GpuTelemetry]]
    health: dict[str, NodeHealth]
    history: dict[str, list[HistoricalIncident]]


CASE_DEFINITIONS = (
    ("thermal-01", IncidentType.THERMAL_THROTTLING, "node-a100-01/gpu-0", "cooling fan degradation"),
    ("thermal-02", IncidentType.THERMAL_THROTTLING, "node-a100-02/gpu-1", "blocked airflow"),
    ("thermal-03", IncidentType.THERMAL_THROTTLING, "node-h100-01/gpu-0", "high ambient temperature"),
    ("ecc-01", IncidentType.ECC_MEMORY_ERROR, "node-a100-03/gpu-1", "degrading HBM memory"),
    ("ecc-02", IncidentType.ECC_MEMORY_ERROR, "node-a100-04/gpu-0", "uncorrectable HBM error"),
    ("ecc-03", IncidentType.ECC_MEMORY_ERROR, "node-h100-02/gpu-1", "rising correctable ECC rate"),
    ("network-01", IncidentType.NETWORK_FAILURE, "node-a100-05", "top-of-rack link failure"),
    ("network-02", IncidentType.NETWORK_FAILURE, "node-a100-06", "NIC driver reset"),
    ("network-03", IncidentType.NETWORK_FAILURE, "node-h100-03", "packet loss on fabric link"),
    ("sensor-01", IncidentType.SENSOR_ANOMALY, "node-a100-07/gpu-0", "fan tachometer sensor glitch"),
    ("overlap-01", IncidentType.NETWORK_FAILURE, "node-h100-04", "fabric link failure with unrelated warm GPU"),
)


def node_for(resource_id: str) -> str:
    return resource_id.split("/")[0]


def build_dataset(seed: int = 20260908) -> FleetDataset:
    """Build a deterministic, intentionally small fleet snapshot for every MVP case."""
    del seed  # Fixture values are deliberately stable and do not depend on runtime randomness.
    base = datetime(2026, 9, 8, 18, 0, tzinfo=UTC)
    all_nodes = tuple(node_for(resource) for _, _, resource, _ in CASE_DEFINITIONS)
    telemetry: dict[str, list[GpuTelemetry]] = {}
    health: dict[str, NodeHealth] = {}
    history: dict[str, list[HistoricalIncident]] = {}
    incidents: dict[str, Incident] = {}

    for index, (case_id, kind, resource, cause) in enumerate(CASE_DEFINITIONS):
        timestamp = (base + timedelta(minutes=index)).isoformat()
        affected_node = node_for(resource)
        incident_resource = resource
        summaries = {
            "sensor-01": f"Cooling subsystem alert reported for {resource}; workload remains available.",
            "overlap-01": f"Distributed training jobs report timeouts and a GPU performance alert on {resource}.",
        }
        incidents[case_id] = Incident(
            incident_id=case_id, incident_type=kind, affected_resource=incident_resource,
            observed_at=timestamp, summary=summaries.get(case_id, f"Synthetic fleet alert reported on {resource}."),
        )
        target_gpu = resource if "/gpu-" in resource else f"{resource}/gpu-0"
        samples = []
        for offset in range(3):
            is_target = offset == 2
            temperature, utilization, power, clock, correctable, uncorrectable, replay = (68.0, 82.0, 300.0, 1410, 0, 0, 0)
            if kind is IncidentType.THERMAL_THROTTLING and is_target:
                temperature, utilization, power, clock = (94.0, 97.0, 350.0, 885)
            elif kind is IncidentType.ECC_MEMORY_ERROR and is_target:
                correctable, uncorrectable = (218, 1 if "02" in case_id else 0)
            elif kind is IncidentType.NETWORK_FAILURE and is_target:
                replay = 46
            if case_id == "overlap-01" and is_target:
                temperature, utilization, power = (84.0, 94.0, 335.0)
                # Keep PCIe healthy: this case isolates fabric loss from a warm-but-subcritical GPU.
                replay = 1
            samples.append(GpuTelemetry(
                timestamp=timestamp, node_id=affected_node, gpu_id=target_gpu.rsplit("/", 1)[-1],
                temperature_c=temperature, utilization_pct=utilization, power_watts=power,
                clock_mhz=clock, ecc_correctable_errors=correctable,
                ecc_uncorrectable_errors=uncorrectable, pcie_replay_errors=replay,
            ))
        telemetry[resource] = samples
        if kind is IncidentType.THERMAL_THROTTLING:
            status, link, loss, latency, fan, messages = "degraded", True, 0.0, 0.3, 450, ["GPU thermal slowdown asserted", "fan speed below target"]
        elif kind is IncidentType.ECC_MEMORY_ERROR:
            status, link, loss, latency, fan, messages = "degraded", True, 0.0, 0.3, 4200, ["NVRM: Xid memory error"]
        elif kind is IncidentType.SENSOR_ANOMALY:
            status, link, loss, latency, fan, messages = "degraded", True, 0.0, 0.3, 0, ["fan tachometer read failure", "no GPU thermal slowdown asserted"]
        else:
            status, link, loss, latency, fan, messages = "unhealthy", False if case_id == "network-01" else True, 18.0, 42.0, 4200, ["network interface link event", "fabric transport timeout"]
        health[affected_node] = NodeHealth(
            node_id=affected_node, observed_at=timestamp, status=status, cpu_utilization_pct=54.0,
            memory_utilization_pct=61.0, network_link_up=link, network_packet_loss_pct=loss,
            network_latency_ms=latency, cooling_fan_rpm=fan, kernel_messages=messages,
        )
        history.setdefault(resource, [])
        if case_id not in {"sensor-01", "overlap-01"}:
            historical = HistoricalIncident(
                incident_id=f"history-{case_id}", observed_at=(base - timedelta(days=14)).isoformat(),
                incident_type=kind, affected_resource=resource,
                resolution=f"Previously investigated: {cause}.",
            )
            history.setdefault(resource, []).append(historical)
            history.setdefault(affected_node, []).append(historical)
    for node in all_nodes:
        history.setdefault(node, [])
    return FleetDataset(incidents=incidents, telemetry=telemetry, health=health, history=history)
