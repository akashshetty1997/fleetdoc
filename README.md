# FleetDoc

FleetDoc is a small local agent that diagnoses synthetic GPU-fleet incidents. It uses OpenAI tool calling to gather telemetry, node-health, and incident-history facts, then returns a validated recommendation-only diagnosis. It is an MVP for measurable diagnosis behavior, not a production fleet controller.

## Architecture

`telemetry.py` creates deterministic fixtures → `tools.py` returns structured facts → `agent.py` calls tools and synthesizes a `Diagnosis` → `mcp_server.py` exposes those same tool functions → `evaluation.py` scores nine cases. Tools do not contain LLM reasoning and no command changes fleet state.

The only MCP tools are:

- `get_telemetry(resource_id)`
- `get_node_health(node_id)`
- `get_recent_incidents(resource_id, limit=5)`

## Setup and CLI

Requires Python 3.12 and an OpenAI API key for live diagnosis.

```bash
python -m pip install -e '.[dev]'
export OPENAI_API_KEY='...'
fleetdoc generate --case thermal-01
fleetdoc diagnose --case thermal-01
fleetdoc evaluate
pytest
```

`generate` works without credentials. `diagnose` prints the incident, concise tool-call names and arguments, and a structured final diagnosis. `evaluate` runs eleven deterministic cases: the original three variations each of thermal throttling, ECC memory error, and network failure, plus a fan-sensor false-positive case and a warm-GPU/network-failure overlap. It passes a case only when both incident type and affected resource match fixture ground truth, then reports accuracy, tool-call count, tools used, and model-marked decisive evidence. Ground-truth incident classes are not sent to the model. Set `FLEETDOC_MODEL` to override the default `gpt-4.1-mini`.

The OpenAI Responses API supplies custom function tools and JSON-schema structured output; see the [official Responses API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create).

## MCP and Claude Code

Run the stdio server with `fleetdoc-mcp`. A Claude Code MCP configuration uses the project interpreter and this command:

```json
{
  "mcpServers": {
    "fleetdoc": { "command": "fleetdoc-mcp" }
  }
}
```

After adding it to your Claude Code MCP configuration, ask Claude Code to list tools and invoke one with `node-a100-01/gpu-0`; its returned object should match the direct CLI/tool response. The test suite also checks wrapper parity.

`AGENTS.md` and `skills/diagnose-fleet-incident/SKILL.md` are active repository instructions for changes to diagnostic behavior. `docs/claude-code-receipts.md` supplies an honest template for recording genuine development sessions.

## Limitations

All fleet data is synthetic and local. Live agent and evaluation results depend on the configured model and API credentials, so no accuracy percentage is claimed here until a run is recorded. There is no dashboard, infrastructure integration, autonomous remediation, GitHub write capability, or production hardening.
