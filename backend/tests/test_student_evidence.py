import unittest
from typing import cast
from uuid import uuid4

from app.curriculum.models import CurriculumEntry
from app.models.student_section import (
    DeterministicValidatorCandidate,
    PracticeItemForPublication,
    PublishPracticeMaterialRequest,
)
from app.services.student_evidence import (
    DeterministicValidationError,
    deterministic_feedback,
    freeze_deterministic_validator,
    prepare_publication_for_attestation,
)
from app.models.teaching_pack import CurriculumObjective


class FakeProvider:
    def __init__(self) -> None:
        self.entry = CurriculumEntry(
            subject="Ciencias Naturales",
            grade_level="6° básico",
            objective=CurriculumObjective(
                code="CN06 OA 15",
                description="Medir y registrar variables observables.",
                source="https://example.test/cn06-oa-15",
            ),
        )

    def find_by_code(self, code: str):
        return self.entry if code == self.entry.objective.code else None


class StudentEvidencePreparationTests(unittest.TestCase):
    def test_frozen_recipe_uses_constrained_sympy_equivalence(self) -> None:
        recipe = freeze_deterministic_validator(
            DeterministicValidatorCandidate(kind="sympy_equivalence", expected_expression="2 + 2")
        )
        self.assertIsNotNone(recipe)
        self.assertTrue(deterministic_feedback(cast(dict, recipe), "4")["matches_expected_answer"])
        self.assertFalse(deterministic_feedback(cast(dict, recipe), "5")["matches_expected_answer"])

    def test_unverified_oa_keeps_practice_item_but_removes_evidence_claim(self) -> None:
        request = PublishPracticeMaterialRequest(
            class_id=uuid4(),
            source_pack_reference="pack-1",
            title="Práctica",
            content_snapshot={"title": "Práctica"},
            declared_objective_codes=["CN06 OA 15", "CN06 OA 99"],
            attestation_statement_version="student-publication-v1",
            items=[
                PracticeItemForPublication(
                    ordinal=1,
                    item_snapshot={"question": "¿Qué observaste?"},
                    requested_evidence_objective_code="CN06 OA 99",
                )
            ],
        )
        prepared = prepare_publication_for_attestation(request, FakeProvider())
        item = prepared.publication.items[0]
        self.assertIsNone(item.evidence_objective_code)
        self.assertEqual(item.evidence_exclusion_reason, "oa_no_verificable")
        self.assertEqual(item.validation_mode, "teacher_judgment")
        self.assertEqual(prepared.excluded_objective_codes, ["CN06 OA 99"])

    def test_unclassified_item_is_teacher_judgment(self) -> None:
        request = PublishPracticeMaterialRequest(
            class_id=uuid4(),
            source_pack_reference="pack-1",
            title="Práctica",
            content_snapshot={"title": "Práctica"},
            attestation_statement_version="student-publication-v1",
            items=[PracticeItemForPublication(ordinal=1, item_snapshot={"question": "Explica por qué."})],
        )
        prepared = prepare_publication_for_attestation(request, FakeProvider())
        self.assertEqual(prepared.publication.items[0].validation_mode, "teacher_judgment")


class DeterministicValidatorAdversarialTests(unittest.TestCase):
    def _freeze(self, expression: str, allowed_symbols: list[str] | None = None) -> dict:
        candidate = DeterministicValidatorCandidate(
            kind="sympy_equivalence",
            expected_expression=expression,
            allowed_symbols=allowed_symbols or [],
        )
        return cast(dict, freeze_deterministic_validator(candidate))

    def test_rejects_import_payload(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("__import__('os').system('x')")

    def test_rejects_dunder_attribute_access(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("().__class__.__bases__[0]")

    def test_rejects_eval_call(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("eval('2+2')")

    def test_rejects_os_system_call(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("os.system('x')")

    def test_rejects_comprehension(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("[i for i in range(9)]")

    def test_rejects_lambda(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("lambda: 1")

    def test_rejects_symbol_outside_allow_list(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("2*y + 1", allowed_symbols=["x"])

    def test_rejects_exponent_bomb(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("2**(3**(3**3))")

    def test_rejects_malformed_expression(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("x*", allowed_symbols=["x"])

    def test_accepts_linear_control(self) -> None:
        recipe = self._freeze("2 + 3*x", allowed_symbols=["x"])
        self.assertEqual(recipe["kind"], "sympy_equivalence")
        self.assertTrue(deterministic_feedback(recipe, "2 + 3*x")["matches_expected_answer"])

    def test_accepts_fractional_control(self) -> None:
        self.assertEqual(self._freeze("x/2 + 0.5", allowed_symbols=["x"])["kind"], "sympy_equivalence")

    def test_accepts_grouped_control(self) -> None:
        self.assertEqual(self._freeze("(x+1)*2", allowed_symbols=["x"])["kind"], "sympy_equivalence")

    def test_accepts_polynomial_control_with_caret(self) -> None:
        self.assertEqual(self._freeze("x^2 + 2*x + 1", allowed_symbols=["x"])["kind"], "sympy_equivalence")

    def test_accepts_maximum_supported_exponent(self) -> None:
        self.assertEqual(self._freeze("x^6 + 1", allowed_symbols=["x"])["kind"], "sympy_equivalence")

    def test_rejects_exponent_above_structural_bound(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("x^7", allowed_symbols=["x"])

    def test_rejects_negative_exponent_below_structural_bound(self) -> None:
        with self.assertRaises(DeterministicValidationError):
            self._freeze("x^-7", allowed_symbols=["x"])

    def test_accepts_division_with_small_reciprocal_exponent(self) -> None:
        self.assertEqual(self._freeze("x/3 + 0.5", allowed_symbols=["x"])["kind"], "sympy_equivalence")
