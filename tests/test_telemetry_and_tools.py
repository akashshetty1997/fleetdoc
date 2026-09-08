import pytest

from fleetdoc.schemas import NodeHealthRequest, RecentIncidentsRequest, TelemetryRequest
from fleetdoc.telemetry import build_dataset
from fleetdoc.tools import ToolInputError, dispatch_tool, get_node_health, get_recent_incidents, get_telemetry, openai_tool_definitions


def test_generation_is_deterministic():
    assert build_dataset().incidents == build_dataset().incidents
    assert len(build_dataset().incidents) == 11


def test_sensor_glitch_has_normal_temperature_without_incident_history():
    dataset = build_dataset()
    assert [sample.temperature_c for sample in dataset.telemetry["node-a100-07/gpu-0"]] == [68.0, 68.0, 68.0]
    assert dataset.history["node-a100-07/gpu-0"] == []


def test_overlap_case_keeps_pcie_replay_errors_at_benign_noise_level():
    samples = build_dataset().telemetry["node-h100-04"]
    assert samples[-1].pcie_replay_errors == 1


def test_tool_responses_are_structured_data_only():
    dataset = build_dataset()
    telemetry = get_telemetry(TelemetryRequest(resource_id="node-a100-01/gpu-0"), dataset)
    health = get_node_health(NodeHealthRequest(node_id="node-a100-01"), dataset)
    history = get_recent_incidents(RecentIncidentsRequest(resource_id="node-a100-01/gpu-0"), dataset)
    assert telemetry.samples[-1].temperature_c == 94.0
    assert health.node.cooling_fan_rpm == 450
    assert history.incidents[0].incident_type == "thermal_throttling"
    assert "diagnos" not in str(telemetry.model_dump()).lower()


def test_malformed_tool_arguments_are_controlled():
    with pytest.raises(ToolInputError, match="Invalid arguments"):
        dispatch_tool("get_telemetry", {"resource_id": 12})
    with pytest.raises(ToolInputError, match="Unsupported"):
        dispatch_tool("invented", {})


def test_strict_openai_schemas_require_every_declared_property():
    recent_incidents = next(tool for tool in openai_tool_definitions() if tool["name"] == "get_recent_incidents")
    assert set(recent_incidents["parameters"]["required"]) == {"resource_id", "limit"}
