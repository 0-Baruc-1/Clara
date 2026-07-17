"""Strict finding matcher with separate attribution near-miss diagnostics."""
from __future__ import annotations

from .schemas import EvaluationCase, ExpectedFinding, MatchResult, MatchedFinding, NearMiss, ObservedFinding


SEVERITY_RANK = {"menor": 1, "importante": 2, "bloqueante": 3}


def _same_anchor(expected: ExpectedFinding, observed: ObservedFinding) -> bool:
    return expected.category == observed.category and expected.target.artifact_type == observed.artifact_type and expected.target.artifact_id == observed.artifact_id


def _strict_match(expected: ExpectedFinding, observed: ObservedFinding) -> bool:
    return _same_anchor(expected, observed) and expected.responsible_agent == observed.responsible_agent


def match_case(case: EvaluationCase, observed: list[ObservedFinding]) -> MatchResult:
    """Match facts, never prose. Attribution near misses stay outside P/R totals."""
    result = MatchResult(case_id=case.id)
    remaining = list(observed)

    emitted = [expected for expected in case.expected if expected.action == "emit"]
    suppressed = [expected for expected in case.expected if expected.action == "suppress"]
    for expected in emitted:
        exact_index = next((index for index, finding in enumerate(remaining) if _strict_match(expected, finding)), None)
        if exact_index is not None:
            finding = remaining.pop(exact_index)
            result.matches.append(MatchedFinding(
                expected_issue_id=expected.issue_id,
                observed_id=finding.id,
                severity_correct=SEVERITY_RANK[finding.severity] >= SEVERITY_RANK[expected.minimum_severity],
            ))
            continue
        near_index = next((index for index, finding in enumerate(remaining) if _same_anchor(expected, finding)), None)
        if near_index is not None:
            finding = remaining.pop(near_index)
            result.near_misses.append(NearMiss(
                expected_issue_id=expected.issue_id,
                observed_id=finding.id,
                expected_agent=expected.responsible_agent,
                observed_agent=finding.responsible_agent,
            ))
            continue
        result.false_negatives.append(expected)

    for expected in suppressed:
        finding_index = next((index for index, finding in enumerate(remaining) if _same_anchor(expected, finding)), None)
        if finding_index is None:
            result.correctly_suppressed.append(expected)
        else:
            result.suppression_violations.append((expected, remaining.pop(finding_index)))

    result.false_positives.extend(remaining)
    return result


def inferred_error_class(finding: ObservedFinding) -> str:
    """Classify unmatched findings for class-specific false-positive rates."""
    if finding.category == "curriculum_honesty" and finding.artifact_type == "plan":
        return "fabricated_oa"
    if finding.category == "grounding" and finding.artifact_type == "assessment_item":
        return "grounding_absent_experiment"
    if finding.category == "objective_coherence" and finding.artifact_type == "plan":
        return "declared_oa_not_worked"
    if finding.category == "objective_coherence" and finding.artifact_type == "assessment_item":
        return "item_not_assessing_claimed_oa"
    if finding.category in {"internal_contradiction", "coverage"} and finding.artifact_type == "activity":
        return "activity_material_gap"
    if finding.category == "internal_contradiction" and finding.artifact_type == "assessment_item":
        return "incorrect_arithmetic_answer"
    return "other"
