import unittest
from unittest.mock import patch

from app.agents.base import AgentContext
from app.agents.reviewer import ReviewerAgent
from app.models.requests import LessonRequest
from app.models.teaching_pack import CurriculumAlignment, CurriculumObjective, ReviewFinding, ReviewReportDraft
from app.services.audit import frame_teacher_edit_findings
from tests.test_review_correction import fixture_assessment, fixture_guide, fixture_plan


class EditedPackReviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_hand_edited_oa_code_is_verified_and_invalid_code_is_blocking(self):
        plan = fixture_plan().model_copy(update={
            "curriculum_alignment": CurriculumAlignment(
                status="partial",
                objectives=[CurriculumObjective(code="CN06 OA 999", description="Código agregado manualmente.", source="Edición")],
            )
        })

        async def parsed_response(*, tool_handler, **_kwargs):
            tool_handler("verificar_objetivo", {"codigo": "CN06 OA 999"})
            return ReviewReportDraft(status="clean", summary="Sin hallazgos del modelo.", findings=[])

        context = AgentContext(LessonRequest(description="Revisar versión editada."), "contexto", "gpt-5.6-luna")
        with patch("app.agents.reviewer.parse_structured_response_with_tools", parsed_response):
            review = await ReviewerAgent().run(context, plan, fixture_guide(), fixture_assessment("Explica el hielo."), teacher_edit_mode=True)

        self.assertEqual(review.status, "findings_remaining")
        self.assertEqual(review.findings[-1].severity, "bloqueante")
        self.assertIn("CN06 OA 999", review.findings[-1].description)

    async def test_absence_finding_is_framed_as_an_observation_of_the_edited_version(self):
        finding = ReviewFinding(
            id="gap", severity="importante", responsible_agent="assessment", category="objective_coherence",
            artifact_type="assessment_item", artifact_id="item-2", description="El objetivo no se evalúa.", suggested_correction="Añade evidencia.",
        )
        framed = frame_teacher_edit_findings([finding])[0]
        self.assertIn("no encontró evidencia explícita", framed.description)
        self.assertNotIn("no se evalúa", framed.description)


if __name__ == "__main__":
    unittest.main()
