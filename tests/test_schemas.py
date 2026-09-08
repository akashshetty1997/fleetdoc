import pytest
from pydantic import ValidationError

from fleetdoc.schemas import Diagnosis, Evidence, IncidentType


def test_diagnosis_confidence_is_bounded():
    with pytest.raises(ValidationError):
        Diagnosis(incident_type=IncidentType.THERMAL_THROTTLING, affected_resource="gpu-0",
                  evidence=[Evidence(source_tool="get_telemetry", observation="hot", decisive=True)], probable_root_cause="fan",
                  confidence=1.1, recommended_action="inspect", escalation_required=False)
