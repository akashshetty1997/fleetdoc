from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from openai import APIError, OpenAI
from pydantic import ValidationError

from .schemas import Diagnosis, Incident
from .telemetry import FleetDataset, build_dataset, node_for
from .tools import ToolInputError, dispatch_tool, openai_tool_definitions

SYSTEM_PROMPT = """You are FleetDoc, an incident diagnosis agent for a synthetic GPU fleet.
Use operational tools to gather structured evidence before diagnosing. You decide which
tools are useful; for the supplied incident, inspect telemetry, node health, and recent
incidents unless a tool is unavailable. Never claim actions were executed: recommend
only safe remediation. Return only the requested diagnosis schema. Evidence must state
concise observed facts and cite its source tool. Mark one or more evidence entries as
decisive only when they materially determine the classification. Do not reveal private reasoning."""


class AgentError(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolTrace:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass(frozen=True)
class AgentResult:
    diagnosis: Diagnosis
    tool_trace: list[ToolTrace]


class FleetDocAgent:
    def __init__(self, client: OpenAI | None = None, model: str | None = None, dataset: FleetDataset | None = None):
        if client is None and not os.environ.get("OPENAI_API_KEY"):
            raise AgentError("OPENAI_API_KEY is required for live FleetDoc diagnosis.")
        self.client = client or OpenAI()
        if not hasattr(self.client, "responses"):
            raise AgentError(
                "The installed OpenAI Python SDK does not support the Responses API. "
                "Run: python3 -m pip install -U 'openai>=1.68.0,<3.0.0'"
            )
        self.model = model or os.environ.get("FLEETDOC_MODEL", "gpt-4.1-mini")
        self.dataset = dataset or build_dataset()

    def diagnose(self, incident: Incident, max_rounds: int = 6) -> AgentResult:
        # Ground truth remains in the fixture for evaluation but is never exposed to the model.
        model_incident = {
            "incident_id": incident.incident_id,
            "affected_resource": incident.affected_resource,
            "observed_at": incident.observed_at,
            "summary": incident.summary,
        }
        input_items: list[dict[str, Any]] = [{"role": "user", "content": json.dumps({
            "incident": model_incident,
            "node_id": node_for(incident.affected_resource),
        })}]
        trace: list[ToolTrace] = []
        response = None
        for _ in range(max_rounds):
            request: dict[str, Any] = {
                "model": self.model,
                "instructions": SYSTEM_PROMPT,
                "tools": openai_tool_definitions(),
                "tool_choice": "auto",
                "text": {"format": {"type": "json_schema", "name": "fleet_diagnosis",
                         "schema": Diagnosis.model_json_schema(), "strict": True}},
            }
            if response is None:
                request["input"] = input_items
            else:
                request["previous_response_id"] = response.id
                request["input"] = input_items
            try:
                response = self.client.responses.create(**request)
            except APIError as exc:
                raise AgentError(f"OpenAI Responses API request failed: {exc}") from exc
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                try:
                    return AgentResult(Diagnosis.model_validate_json(response.output_text), trace)
                except ValidationError as exc:
                    raise AgentError(f"Model returned invalid final diagnosis: {exc}") from exc
            input_items = []
            for call in calls:
                try:
                    args = json.loads(call.arguments)
                    result = dispatch_tool(call.name, args, self.dataset)
                except (json.JSONDecodeError, ToolInputError) as exc:
                    result = {"error": str(exc)}
                else:
                    trace.append(ToolTrace(name=call.name, arguments=args, result=result))
                input_items.append({"type": "function_call_output", "call_id": call.call_id,
                                    "output": json.dumps(result)})
        raise AgentError(f"Model did not produce a final diagnosis after {max_rounds} tool rounds.")
