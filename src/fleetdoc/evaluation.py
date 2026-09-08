from __future__ import annotations

from dataclasses import dataclass

from .agent import FleetDocAgent
from .schemas import Diagnosis, Incident
from .telemetry import FleetDataset, build_dataset


@dataclass(frozen=True)
class EvaluationCase:
    incident: Incident
    expected_type: str
    expected_resource: str


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    diagnosis: Diagnosis
    passed: bool
    tool_call_count: int
    tool_names: list[str]
    decisive_evidence: list[str]


def evaluation_cases(dataset: FleetDataset | None = None) -> list[EvaluationCase]:
    dataset = dataset or build_dataset()
    return [EvaluationCase(incident=item, expected_type=item.incident_type.value,
                           expected_resource=item.affected_resource)
            for item in dataset.incidents.values()]


def is_pass(case: EvaluationCase, diagnosis: Diagnosis) -> bool:
    return diagnosis.incident_type.value == case.expected_type and diagnosis.affected_resource == case.expected_resource


def run_evaluation(agent: FleetDocAgent, dataset: FleetDataset | None = None) -> list[EvaluationResult]:
    return [EvaluationResult(
                case.incident.incident_id,
                outcome.diagnosis,
                is_pass(case, outcome.diagnosis),
                len(outcome.tool_trace),
                [event.name for event in outcome.tool_trace],
                [evidence.observation for evidence in outcome.diagnosis.evidence if evidence.decisive],
            )
            for case in evaluation_cases(dataset) for outcome in [agent.diagnose(case.incident)]]


def accuracy(results: list[EvaluationResult]) -> float:
    return sum(result.passed for result in results) / len(results) if results else 0.0
