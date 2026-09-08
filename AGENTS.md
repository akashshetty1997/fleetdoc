# FleetDoc development rules

## Mission and architecture

FleetDoc diagnoses deterministic, synthetic GPU fleet incidents. `telemetry.py` owns fixtures; `tools.py` only retrieves validated data; `agent.py` alone synthesizes evidence and recommendations; `mcp_server.py` only exposes the same tools; `evaluation.py` scores diagnoses.

## Commands

```bash
python -m pip install -e '.[dev]'
fleetdoc generate --case thermal-01
fleetdoc diagnose --case thermal-01
fleetdoc evaluate
fleetdoc-mcp
pytest
```

Set `OPENAI_API_KEY` before `diagnose` or `evaluate`; set `FLEETDOC_MODEL` to override `gpt-4.1-mini`.

## Engineering and safety rules

- Keep exactly three operational tools: telemetry, node health, and recent incidents.
- Tools return validated structured facts only. Never add diagnosis, LLM calls, or side effects to them.
- The agent must ground every diagnosis in tool evidence and produce the `Diagnosis` schema.
- Recommendations are advisory only: never execute remediation or mutate infrastructure.
- Keep synthetic fixtures deterministic and give every evaluation incident ground truth.
- Add or adjust tests with changes to schemas, fixtures, tool contracts, scoring, or agent behavior.

## Required diagnostic workflow

Read `skills/diagnose-fleet-incident/SKILL.md` before modifying diagnosis behavior or adding telemetry signals. Preserve the data/tool/agent/MCP boundary.

## Claude Code receipt protocol

For a controlled extension task, ask Claude Code to add one non-diagnostic telemetry field and its test after reading this file and the skill. Review that it does not add a tool, place diagnosis in data code, or change safety behavior. Record only a genuine session in `docs/claude-code-receipts.md` using its template.
