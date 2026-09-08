from __future__ import annotations

from collections.abc import Callable

from .schemas import (
    NodeHealthRequest, NodeHealthResponse, RecentIncidentsRequest, RecentIncidentsResponse,
    TelemetryRequest, TelemetryResponse,
)
from .telemetry import FleetDataset, build_dataset, node_for


class ToolInputError(ValueError):
    pass


def get_telemetry(request: TelemetryRequest, dataset: FleetDataset | None = None) -> TelemetryResponse:
    dataset = dataset or build_dataset()
    samples = dataset.telemetry.get(request.resource_id)
    if samples is None:
        raise ToolInputError(f"Unknown telemetry resource: {request.resource_id}")
    return TelemetryResponse(resource_id=request.resource_id, samples=samples)


def get_node_health(request: NodeHealthRequest, dataset: FleetDataset | None = None) -> NodeHealthResponse:
    dataset = dataset or build_dataset()
    health = dataset.health.get(request.node_id)
    if health is None:
        raise ToolInputError(f"Unknown node: {request.node_id}")
    return NodeHealthResponse(node=health)


def get_recent_incidents(request: RecentIncidentsRequest, dataset: FleetDataset | None = None) -> RecentIncidentsResponse:
    dataset = dataset or build_dataset()
    resource_id = request.resource_id
    records = dataset.history.get(resource_id)
    if records is None and "/gpu-" in resource_id:
        records = dataset.history.get(node_for(resource_id), [])
    if records is None:
        raise ToolInputError(f"Unknown incident resource: {resource_id}")
    return RecentIncidentsResponse(resource_id=resource_id, incidents=records[:request.limit])


TOOL_MODELS = {
    "get_telemetry": (TelemetryRequest, get_telemetry),
    "get_node_health": (NodeHealthRequest, get_node_health),
    "get_recent_incidents": (RecentIncidentsRequest, get_recent_incidents),
}


def openai_tool_definitions() -> list[dict]:
    descriptions = {
        "get_telemetry": "Retrieve GPU metrics for one GPU resource. Data only; no diagnosis.",
        "get_node_health": "Retrieve node health and network state for one node. Data only; no diagnosis.",
        "get_recent_incidents": "Retrieve historical incidents for a resource or its node. Data only; no diagnosis.",
    }
    def strict_schema(schema: dict) -> dict:
        """Apply the OpenAI strict-function requirement to Pydantic's JSON Schema.

        OpenAI requires `required` to include every property under strict mode,
        even when Pydantic represents a Python default as an optional field.
        The Python/MCP interface may still omit that field and use its default.
        """
        schema = dict(schema)
        properties = schema.get("properties")
        if properties:
            schema["required"] = list(properties)
            schema["additionalProperties"] = False
        for key in ("$defs",):
            if key in schema:
                schema[key] = {name: strict_schema(value) for name, value in schema[key].items()}
        return schema

    return [
        {"type": "function", "name": name, "description": descriptions[name],
         "parameters": strict_schema(model.model_json_schema()), "strict": True}
        for name, (model, _) in TOOL_MODELS.items()
    ]


def dispatch_tool(name: str, arguments: dict, dataset: FleetDataset | None = None) -> dict:
    try:
        request_model, handler = TOOL_MODELS[name]
    except KeyError as exc:
        raise ToolInputError(f"Unsupported tool: {name}") from exc
    try:
        request = request_model.model_validate(arguments)
    except Exception as exc:
        raise ToolInputError(f"Invalid arguments for {name}: {exc}") from exc
    return handler(request, dataset).model_dump(mode="json")
