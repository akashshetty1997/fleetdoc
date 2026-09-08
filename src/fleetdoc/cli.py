from __future__ import annotations

import argparse
import json

from .agent import AgentError, FleetDocAgent
from .evaluation import accuracy, run_evaluation
from .telemetry import build_dataset


def _dataset_case(case_id: str):
    dataset = build_dataset()
    try:
        return dataset, dataset.incidents[case_id]
    except KeyError as exc:
        choices = ", ".join(dataset.incidents)
        raise SystemExit(f"Unknown case {case_id!r}. Available cases: {choices}") from exc


def _print_diagnosis(agent: FleetDocAgent, case_id: str) -> None:
    _, incident = _dataset_case(case_id)
    print("Incident:")
    print(json.dumps(incident.model_dump(mode="json"), indent=2))
    result = agent.diagnose(incident)
    print("\nTool calls:")
    for event in result.tool_trace:
        print(f"- {event.name}({json.dumps(event.arguments, sort_keys=True)})")
    print("\nDiagnosis:")
    print(result.diagnosis.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="FleetDoc synthetic GPU incident diagnosis")
    commands = parser.add_subparsers(dest="command", required=True)
    generate = commands.add_parser("generate", help="Print a deterministic incident")
    generate.add_argument("--case", default="thermal-01")
    diagnose = commands.add_parser("diagnose", help="Run a live diagnosis")
    diagnose.add_argument("--case", default="thermal-01")
    commands.add_parser("evaluate", help="Run all nine live evaluation cases")
    args = parser.parse_args()
    if args.command == "generate":
        _, incident = _dataset_case(args.case)
        print(incident.model_dump_json(indent=2))
        return
    try:
        agent = FleetDocAgent(dataset=build_dataset())
    except AgentError as exc:
        parser.error(str(exc))
    if args.command == "diagnose":
        try:
            _print_diagnosis(agent, args.case)
        except AgentError as exc:
            parser.error(str(exc))
        return
    try:
        results = run_evaluation(agent)
    except AgentError as exc:
        parser.error(str(exc))
    for result in results:
        print(json.dumps({"case_id": result.case_id, "predicted_incident_type": result.diagnosis.incident_type,
                          "affected_resource": result.diagnosis.affected_resource, "confidence": result.diagnosis.confidence,
                          "tool_call_count": result.tool_call_count, "tool_names": result.tool_names,
                          "decisive_evidence": result.decisive_evidence, "pass": result.passed}))
    print(f"accuracy={accuracy(results):.1%} ({sum(r.passed for r in results)}/{len(results)})")


if __name__ == "__main__":
    main()
