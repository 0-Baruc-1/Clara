import unittest

from app.agents.reviewer import _cited_curriculum_codes


class ReviewerCodeNormalizationTests(unittest.TestCase):
    def test_short_oa_reference_reuses_the_declared_full_code(self):
        codes = _cited_curriculum_codes(
            "La actividad trabaja OA 13 y el plan cita CN06 OA 13.",
            {"CN06 OA 13"},
        )
        self.assertEqual(codes, {"CN06 OA 13"})

    def test_ambiguous_short_oa_reference_is_not_a_fake_verification_code(self):
        codes = _cited_curriculum_codes(
            "La actividad menciona OA 13.",
            {"CN06 OA 13", "MA06 OA 13"},
        )
        self.assertEqual(codes, set())

