import os

import pytest

from fleetdoc.agent import FleetDocAgent
from fleetdoc.telemetry import build_dataset


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not configured")
def test_seeded_incident_uses_all_three_tools_live():
    dataset = build_dataset()
    result = FleetDocAgent(dataset=dataset).diagnose(dataset.incidents["thermal-01"])
    assert {entry.name for entry in result.tool_trace} == {"get_telemetry", "get_node_health", "get_recent_incidents"}
    assert result.diagnosis.affected_resource == "node-a100-01/gpu-0"
