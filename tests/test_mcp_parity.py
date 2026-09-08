import anyio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from fleetdoc.mcp_server import get_node_health_mcp, get_recent_incidents_mcp, get_telemetry_mcp
from fleetdoc.schemas import NodeHealthRequest, RecentIncidentsRequest, TelemetryRequest
from fleetdoc.tools import get_node_health, get_recent_incidents, get_telemetry


def test_mcp_wrappers_match_shared_operational_tools():
    assert get_telemetry_mcp("node-a100-01/gpu-0") == get_telemetry(TelemetryRequest(resource_id="node-a100-01/gpu-0")).model_dump(mode="json")
    assert get_node_health_mcp("node-a100-01") == get_node_health(NodeHealthRequest(node_id="node-a100-01")).model_dump(mode="json")
    assert get_recent_incidents_mcp("node-a100-01/gpu-0") == get_recent_incidents(RecentIncidentsRequest(resource_id="node-a100-01/gpu-0")).model_dump(mode="json")


def test_stdio_mcp_server_discovers_and_invokes_a_tool():
    async def invoke() -> None:
        params = StdioServerParameters(command="fleetdoc-mcp")
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert {tool.name for tool in listed.tools} == {"get_telemetry", "get_node_health", "get_recent_incidents"}
                result = await session.call_tool("get_telemetry", {"resource_id": "node-a100-01/gpu-0"})
                assert result.isError is False
                assert "temperature_c" in result.content[0].text
    anyio.run(invoke)
