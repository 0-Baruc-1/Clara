import unittest

from evals.cases import CASES
from evals.matcher import match_case
from evals.metrics import summarize
from evals.mock_adapter import DeterministicMockReviewer
from evals.schemas import EvaluationCase, ExpectedFinding, ObservedFinding


class ReviewerEvaluationHarnessTest(unittest.TestCase):
    def test_hand_written_suite_has_agreed_case_counts(self) -> None:
        self.assertEqual(len(CASES), 68)
        self.assertEqual(sum(case.kind == "control" for case in CASES), 10)
        self.assertEqual(sum(case.kind == "audit_gate" for case in CASES), 16)
        self.assertEqual(sum(case.kind == "error" and case.provenance == "synthetic" for case in CASES), 40)
        self.assertEqual(sum(case.kind == "error" and case.provenance == "captured" for case in CASES), 2)
        self.assertEqual({case.baseline_id for case in CASES}, {"cn_water_states_v1", "cn_energy_v1", "ma_percentages_v1", "ma_geometry_v1"})

    def test_mock_adapter_proves_deterministic_harness_path(self) -> None:
        adapter = DeterministicMockReviewer()
        results = {case.id: match_case(case, adapter.run(case)) for case in CASES}
        report = summarize(results)
        self.assertEqual(report["case_counts"]["total"], 68)
        self.assertEqual(report["precision_gate"]["suppression_rate"], 1.0)
        self.assertEqual(report["precision_gate"]["presence_emission_rate"], 1.0)
        for values in report["per_error_class"].values():
            self.assertEqual(values["recall"], 1.0)
            self.assertEqual(values["precision"], 1.0)

    def test_agent_attribution_near_miss_is_diagnostic_not_fp_or_fn(self) -> None:
        case = next(case for case in CASES if case.id == "synthetic-false-alignment-cn-water-oa13")
        expected = case.expected[0]
        wrong_agent = ObservedFinding(
            id="wrong-agent",
            severity="importante",
            responsible_agent="designer",
            category=expected.category,
            artifact_type=expected.target.artifact_type,
            artifact_id=expected.target.artifact_id,
        )
        result = match_case(case, [wrong_agent])
        self.assertEqual(len(result.near_misses), 1)
        self.assertEqual(result.false_positives, [])
        self.assertEqual(result.false_negatives, [])

    def test_unexpected_control_finding_counts_as_false_positive(self) -> None:
        control = next(case for case in CASES if case.id == "control-01")
        finding = ObservedFinding(
            id="unexpected",
            severity="importante",
            responsible_agent="assessment",
            category="internal_contradiction",
            artifact_type="assessment_item",
            artifact_id="water-item-1",
        )
        result = match_case(control, [finding])
        self.assertEqual(len(result.false_positives), 1)
        self.assertEqual(result.false_negatives, [])


if __name__ == "__main__":
    unittest.main()
