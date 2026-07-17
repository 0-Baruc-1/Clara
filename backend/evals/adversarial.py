"""Hand-authored adversarial mock outputs used to calibrate the harness."""
from __future__ import annotations

from copy import deepcopy

from .cases import CASES, cases_by_id
from .mock_adapter import DeterministicMockReviewer
from .schemas import ObservedFinding


SCENARIOS = (
    "omitted_expected_finding",
    "false_positive_on_control",
    "wrong_responsible_agent",
    "low_confidence_absence_emitted",
    "host_enforced_segregation",
    "wrong_artifact_id",
)


def baseline_outputs() -> dict[str, list[ObservedFinding]]:
    adapter = DeterministicMockReviewer()
    return {case.id: adapter.run(case) for case in CASES}


def _expected_observed(case_id: str) -> ObservedFinding:
    case = cases_by_id()[case_id]
    # Suppressed gate cases need a deliberately injected observation too.
    expected = case.expected[0]
    return ObservedFinding(
        id=f"adversarial-{expected.issue_id}",
        severity=expected.minimum_severity,
        responsible_agent=expected.responsible_agent,
        category=expected.category,
        artifact_type=expected.target.artifact_type,
        artifact_id=expected.target.artifact_id,
        origin=expected.detection_origin,
    )


def outputs_for(scenario: str) -> dict[str, list[ObservedFinding]]:
    if scenario not in SCENARIOS:
        raise ValueError(f"Escenario adversarial desconocido: {scenario}")
    outputs = baseline_outputs()
    if scenario == "omitted_expected_finding":
        outputs["synthetic-arithmetic-ma-percent-answer-1"] = []
    elif scenario == "false_positive_on_control":
        outputs["control-01"].append(ObservedFinding(
            id="adversarial-control-fp",
            severity="importante",
            responsible_agent="assessment",
            category="internal_contradiction",
            artifact_type="assessment_item",
            artifact_id="water-item-1",
        ))
    elif scenario == "wrong_responsible_agent":
        case_id = "synthetic-false-alignment-cn-water-oa13"
        expected = _expected_observed(case_id)
        outputs[case_id] = [
            ObservedFinding(
                id="adversarial-wrong-agent",
                severity=expected.severity,
                responsible_agent="designer",
                category=expected.category,
                artifact_type=expected.artifact_type,
                artifact_id=expected.artifact_id,
                origin=expected.origin,
            )
        ]
    elif scenario == "low_confidence_absence_emitted":
        outputs["gate-01-baja"] = [_expected_observed("gate-01-baja")]
    elif scenario == "host_enforced_segregation":
        # Baseline output already contains all twelve hand-authored host findings.
        pass
    elif scenario == "wrong_artifact_id":
        case_id = "synthetic-item-alignment-cn-water-item1"
        expected = _expected_observed(case_id)
        outputs[case_id] = [
            ObservedFinding(
                id="adversarial-wrong-artifact",
                severity=expected.severity,
                responsible_agent=expected.responsible_agent,
                category=expected.category,
                artifact_type=expected.artifact_type,
                artifact_id="water-item-unrelated",
                origin=expected.origin,
            )
        ]
    return outputs
