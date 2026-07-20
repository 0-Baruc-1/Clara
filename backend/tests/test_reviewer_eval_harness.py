import unittest

from evals.adversarial import outputs_for
from evals.cases import CASES
from evals.matcher import match_case
from evals.metrics import summarize
from evals.mock_adapter import DeterministicMockReviewer
from evals.material_factory import build_case_material
from evals.schemas import EvaluationCase, ExpectedFinding, ObservedFinding


class ReviewerEvaluationHarnessTest(unittest.TestCase):
    def _scenario(self, name: str) -> dict[str, object]:
        outputs = outputs_for(name)
        return summarize({case.id: match_case(case, outputs[case.id]) for case in CASES})

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
        self.assertEqual(report["model_reasoning_score"]["true_positives"], 40)
        self.assertEqual(report["host_enforced_results_excluded_from_model_reasoning"]["matched"], 12)
        self.assertEqual(report["model_reasoning_denominator"], {"synthetic_error": 32, "captured_error": 2, "audit_gate_emit": 6, "total": 40})
        self.assertEqual(report["host_enforced_denominator"], {"synthetic_error": 8, "captured_error": 0, "audit_gate_emit": 4, "total": 12})
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

    def test_cross_type_agent_attribution_is_also_a_near_miss(self) -> None:
        case = next(case for case in CASES if case.id == "synthetic-material-gap-cn-energy-battery")
        expected = case.expected[0]
        observed = ObservedFinding(
            id="battery-materials-agent",
            severity="bloqueante",
            responsible_agent="materials",
            category=expected.category,
            artifact_type="material",
            artifact_id="energy-test",
        )
        result = match_case(case, [observed])
        self.assertEqual(len(result.near_misses), 1)
        self.assertEqual(result.near_misses[0].expected_artifact_type, "activity")
        self.assertEqual(result.near_misses[0].observed_artifact_type, "material")
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

    def test_adversarial_omission_has_hand_computed_recall(self) -> None:
        report = self._scenario("omitted_expected_finding")
        arithmetic = report["per_error_class"]["incorrect_arithmetic_answer"]
        self.assertEqual((arithmetic["true_positives"], arithmetic["false_negatives"]), (7, 1))
        self.assertEqual(arithmetic["recall"], 7 / 8)
        self.assertEqual(report["model_reasoning_score"]["recall"], 39 / 40)

    def test_adversarial_control_finding_has_hand_computed_fpr(self) -> None:
        report = self._scenario("false_positive_on_control")
        arithmetic = report["per_error_class"]["incorrect_arithmetic_answer"]
        self.assertEqual((arithmetic["true_positives"], arithmetic["false_positives"]), (8, 1))
        self.assertEqual(arithmetic["precision"], 8 / 9)
        self.assertEqual(arithmetic["control_false_positive_rate"], 1 / 10)
        self.assertEqual(report["model_reasoning_score"]["precision"], 40 / 41)

    def test_adversarial_wrong_agent_is_only_a_near_miss(self) -> None:
        report = self._scenario("wrong_responsible_agent")
        false_alignment = report["per_error_class"]["declared_oa_not_worked"]
        self.assertEqual((false_alignment["true_positives"], false_alignment["false_positives"], false_alignment["false_negatives"]), (11, 0, 0))
        self.assertEqual((false_alignment["precision"], false_alignment["recall"]), (1.0, 1.0))
        self.assertEqual(len(report["near_misses_excluded_from_precision_and_recall"]), 1)

    def test_adversarial_low_confidence_absence_is_gate_violation_only(self) -> None:
        report = self._scenario("low_confidence_absence_emitted")
        gate = report["precision_gate"]
        self.assertEqual((gate["expected_suppress"], gate["suppressed"], gate["violations"]), (6, 5, 1))
        self.assertEqual(gate["suppression_rate"], 5 / 6)
        self.assertEqual(report["model_reasoning_score"]["true_positives"], 40)
        self.assertEqual(report["model_reasoning_score"]["false_positives"], 0)

    def test_host_enforced_findings_do_not_inflate_reasoning_score(self) -> None:
        report = self._scenario("host_enforced_segregation")
        fabricated = report["per_error_class"]["fabricated_oa"]
        self.assertEqual(fabricated["true_positives"], 12)
        self.assertEqual(report["host_enforced_results_excluded_from_model_reasoning"]["matched"], 12)
        self.assertEqual(report["model_reasoning_score"]["true_positives"], 40)
        self.assertEqual(report["model_reasoning_score"]["recall"], 1.0)

    def test_wrong_artifact_id_is_one_fp_and_one_fn(self) -> None:
        report = self._scenario("wrong_artifact_id")
        item_alignment = report["per_error_class"]["item_not_assessing_claimed_oa"]
        self.assertEqual(
            (item_alignment["true_positives"], item_alignment["false_positives"], item_alignment["false_negatives"]),
            (10, 1, 1),
        )
        self.assertEqual(item_alignment["precision"], 10 / 11)
        self.assertEqual(item_alignment["recall"], 10 / 11)

    def test_real_adapter_fixtures_are_typed_and_apply_host_mutation(self) -> None:
        case = next(case for case in CASES if case.id == "synthetic-fabricated-oa-cn-water-999")
        plan, activities, assessment = build_case_material(case)
        self.assertIn("CN06 OA 99", [objective.code for objective in plan.curriculum_alignment.objectives])
        self.assertIn("CN06 OA 99", plan.learning_objectives)
        self.assertEqual(activities.activities[0].id, "water-observe")
        self.assertEqual(assessment.items[0].id, "water-item-1")

    def test_real_adapter_fixture_injects_freezer_without_activity_evidence(self) -> None:
        case = next(case for case in CASES if case.id == "captured-freezer-grounding")
        _, activities, assessment = build_case_material(case)
        self.assertIn("freezer", assessment.items[0].question)
        self.assertFalse(any("freezer" in activity.title.casefold() for activity in activities.activities))


if __name__ == "__main__":
    unittest.main()
