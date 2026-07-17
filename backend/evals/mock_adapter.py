"""Deterministic adapter for testing the harness, never Reviewer performance."""
from __future__ import annotations

from .schemas import EvaluationCase, ObservedFinding


class DeterministicMockReviewer:
    """Returns hand-authored expected emitted findings exactly.

    This intentionally proves only the evaluator's case, matching and reporting
    paths. Real-model metrics are available only in milestone 2.
    """

    def run(self, case: EvaluationCase) -> list[ObservedFinding]:
        return [
            ObservedFinding(
                id=f"mock-{expected.issue_id}",
                severity=expected.minimum_severity,
                responsible_agent=expected.responsible_agent,
                category=expected.category,
                artifact_type=expected.target.artifact_type,
                artifact_id=expected.target.artifact_id,
                description="Salida determinista del adaptador mock del harness.",
            )
            for expected in case.expected
            if expected.action == "emit"
        ]
