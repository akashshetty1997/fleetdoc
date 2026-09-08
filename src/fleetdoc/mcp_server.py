from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .schemas import NodeHealthRequest, RecentIncidentsRequest, TelemetryRequest
from .tools import get_node_health, get_recent_incidents, get_telemetry

mcp = FastMCP("FleetDoc")


@mcp.tool(name="get_telemetry", description="Retrieve GPU telemetry for one GPU resource. Returns data only; no diagnosis.")
def get_telemetry_mcp(resource_id: str) -> dict:
    return get_telemetry(TelemetryRequest(resource_id=resource_id)).model_dump(mode="json")


@mcp.tool(name="get_node_health", description="Retrieve health and network state for one node. Returns data only; no diagnosis.")
def get_node_health_mcp(node_id: str) -> dict:
    return get_node_health(NodeHealthRequest(node_id=node_id)).model_dump(mode="json")


@mcp.tool(name="get_recent_incidents", description="Retrieve recent historical incidents for a GPU resource or node. Returns data only; no diagnosis.")
def get_recent_incidents_mcp(resource_id: str, limit: int = 5) -> dict:
    return get_recent_incidents(RecentIncidentsRequest(resource_id=resource_id, limit=limit)).model_dump(mode="json")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
