from fleetdoc.evaluation import EvaluationResult, accuracy, evaluation_cases, is_pass
from fleetdoc.schemas import Diagnosis, Evidence


def diagnosis_for(case, resource=None):
    return Diagnosis(incident_type=case.incident.incident_type, affected_resource=resource or case.expected_resource,
                     evidence=[Evidence(source_tool="get_telemetry", observation="A controlled fixture signal was observed.", decisive=True)],
                     probable_root_cause="fixture", confidence=0.9, recommended_action="Inspect and replace failed hardware if confirmed.",
                     escalation_required=True)


def test_nine_ground_truth_cases_and_pass_rule():
    cases = evaluation_cases()
    assert len(cases) == 11
    assert {case.expected_type for case in cases} == {"thermal_throttling", "ecc_memory_error", "network_failure", "sensor_anomaly"}
    assert is_pass(cases[0], diagnosis_for(cases[0]))
    assert not is_pass(cases[0], diagnosis_for(cases[0], "wrong-resource"))


def test_accuracy():
    case = evaluation_cases()[0]
    passed = EvaluationResult(case.incident.incident_id, diagnosis_for(case), True, 3, ["get_telemetry"], ["fixture"])
    failed = EvaluationResult(case.incident.incident_id, diagnosis_for(case, "wrong"), False, 3, ["get_telemetry"], ["fixture"])
    assert accuracy([passed, failed]) == 0.5
