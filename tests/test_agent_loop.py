import json
from types import SimpleNamespace

from fleetdoc.agent import FleetDocAgent
from fleetdoc.telemetry import build_dataset


class FakeResponses:
    def __init__(self):
        self.requests = []
        self.count = 0

    def create(self, **kwargs):
        self.requests.append(kwargs)
        self.count += 1
        if self.count == 1:
            calls = [
                SimpleNamespace(type="function_call", name="get_telemetry", arguments='{"resource_id":"node-a100-01/gpu-0"}', call_id="one"),
                SimpleNamespace(type="function_call", name="get_node_health", arguments='{"node_id":"node-a100-01"}', call_id="two"),
                SimpleNamespace(type="function_call", name="get_recent_incidents", arguments='{"resource_id":"node-a100-01/gpu-0"}', call_id="three"),
            ]
            return SimpleNamespace(id="response-1", output=calls, output_text="")
        diagnosis = {"incident_type": "thermal_throttling", "affected_resource": "node-a100-01/gpu-0",
                     "evidence": [{"source_tool": "get_telemetry", "observation": "Temperature is 94C and clock is reduced.", "decisive": True}],
                     "probable_root_cause": "Cooling fault", "confidence": 0.92,
                     "recommended_action": "Inspect cooling and drain the node if temperature persists.",
                     "escalation_required": True}
        return SimpleNamespace(id="response-2", output=[], output_text=json.dumps(diagnosis))


def test_agent_loop_dispatches_model_selected_tools_and_validates_diagnosis():
    responses = FakeResponses()
    agent = FleetDocAgent(client=SimpleNamespace(responses=responses), dataset=build_dataset())
    result = agent.diagnose(build_dataset().incidents["thermal-01"])
    assert [event.name for event in result.tool_trace] == ["get_telemetry", "get_node_health", "get_recent_incidents"]
    assert result.diagnosis.confidence == 0.92
    assert responses.requests[1]["previous_response_id"] == "response-1"
    assert "incident_type" not in responses.requests[0]["input"][0]["content"]
