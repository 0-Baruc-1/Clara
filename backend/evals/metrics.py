"""Metric aggregation for strict matches and precision-gate outcomes."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict

from .cases import CASES
from .matcher import inferred_error_class
from .schemas import MatchResult


PRIMARY_CLASSES = (
    "declared_oa_not_worked",
    "item_not_assessing_claimed_oa",
    "incorrect_arithmetic_answer",
    "activity_material_gap",
    "fabricated_oa",
)


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def summarize(results: dict[str, MatchResult]) -> dict[str, object]:
    case_by_id = {case.id: case for case in CASES}
    counts = {error_class: {"tp": 0, "fp": 0, "fn": 0, "severity_correct": 0, "severity_observed": 0, "control_fp_cases": set()} for error_class in PRIMARY_CLASSES}
    near_misses: list[dict[str, object]] = []
    gate = {"expected_emit": 0, "emitted": 0, "expected_suppress": 0, "suppressed": 0, "violations": 0}
    controls = [case for case in CASES if case.kind == "control"]

    for case_id, result in results.items():
        case = case_by_id[case_id]
        for match in result.matches:
            expected = next(item for item in case.expected if item.issue_id == match.expected_issue_id)
            if expected.error_class in counts:
                counts[expected.error_class]["tp"] += 1
                counts[expected.error_class]["severity_observed"] += 1
                counts[expected.error_class]["severity_correct"] += int(match.severity_correct)
            if case.kind == "audit_gate":
                gate["expected_emit"] += 1
                gate["emitted"] += 1
        for expected in result.false_negatives:
            if expected.error_class in counts:
                counts[expected.error_class]["fn"] += 1
            if case.kind == "audit_gate":
                gate["expected_emit"] += 1
        for expected in result.correctly_suppressed:
            if case.kind == "audit_gate":
                gate["expected_suppress"] += 1
                gate["suppressed"] += 1
        for expected, _ in result.suppression_violations:
            if case.kind == "audit_gate":
                gate["expected_suppress"] += 1
                gate["violations"] += 1
        for finding in result.false_positives:
            error_class = inferred_error_class(finding)
            if error_class in counts:
                counts[error_class]["fp"] += 1
                if case.kind == "control":
                    counts[error_class]["control_fp_cases"].add(case.id)
        for near in result.near_misses:
            near_misses.append(asdict(near) | {"case_id": case.id})

    per_class = {}
    for error_class, row in counts.items():
        tp, fp, fn = row["tp"], row["fp"], row["fn"]
        per_class[error_class] = {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": _ratio(tp, tp + fp),
            "recall": _ratio(tp, tp + fn),
            "control_false_positive_rate": _ratio(len(row["control_fp_cases"]), len(controls)),
            "severity_accuracy_among_true_positives": _ratio(row["severity_correct"], row["severity_observed"]),
        }

    return {
        "case_counts": {
            "total": len(CASES),
            "synthetic_error_cases": sum(case.kind == "error" and case.provenance == "synthetic" for case in CASES),
            "captured_error_cases": sum(case.kind == "error" and case.provenance == "captured" for case in CASES),
            "controls": len(controls),
            "audit_gate_cases": sum(case.kind == "audit_gate" for case in CASES),
        },
        "per_error_class": per_class,
        "near_misses_excluded_from_precision_and_recall": near_misses,
        "precision_gate": {
            **gate,
            "suppression_rate": _ratio(gate["suppressed"], gate["expected_suppress"]),
            "presence_emission_rate": _ratio(gate["emitted"], gate["expected_emit"]),
        },
    }
