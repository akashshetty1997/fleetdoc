# Diagnose Fleet Incident

## Purpose and use

Use this skill when implementing, changing, reviewing, or evaluating FleetDoc diagnosis behavior. Read `AGENTS.md` first.

## Required inputs

An incident identifier, affected resource, deterministic telemetry dataset, and the three tool contracts are required. Do not infer unavailable facts.

## Procedure

1. Identify the affected node from the incident resource.
2. Retrieve telemetry, node health, and recent incidents as warranted by the incident.
3. Record concise observations that name the source tool.
4. Have the agent—not a data tool—classify the incident and synthesize probable cause.
5. Validate the exact `Diagnosis` schema before returning it.

## Evidence, confidence, and remediation

Evidence must be factual, short, and traceable to a tool result. Confidence is a number from 0 through 1 and reflects evidence strength, not certainty. Recommend investigation, draining, replacement, or escalation only; never perform a production action. Escalate for uncorrectable ECC, persistent overheating, or fabric/network loss affecting workloads.

## Output format

Return `incident_type`, `affected_resource`, `evidence`, `probable_root_cause`, `confidence`, `recommended_action`, and `escalation_required`. Do not emit hidden reasoning or prose outside that structured diagnosis.
