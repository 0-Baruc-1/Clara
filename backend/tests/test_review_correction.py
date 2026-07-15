"""Deterministic proof that the Reviewer correction loop is not a blind re-run."""
import asyncio
import json
import unittest
from unittest.mock import patch

from app.models.requests import LessonRequest
from app.models.teaching_pack import (
    ActivityDifferentiation,
    ActivityGuide,
    Assessment,
    AssessmentItem,
    ClassroomActivity,
    CurriculumAlignment,
    LessonPlan,
    LessonStage,
    ReviewFinding,
    ReviewReport,
    RubricCriterion,
    RubricLevels,
    SpecificationRow,
)


OBJECTIVE = "Explicar cambios de estado del agua."


def fixture_plan() -> LessonPlan:
    return LessonPlan(
        title="Cambios de estado", subject="Ciencias Naturales", grade_level="6° básico",
        duration_minutes=45, curriculum_alignment=CurriculumAlignment(status="not_found"),
        learning_objectives=[OBJECTIVE], key_concepts=["Cambios de estado"],
        prerequisite_knowledge=["Estados de la materia"], materials=["Vaso"],
        stages=[LessonStage(name="Desarrollo", duration_minutes=35, purpose="Explorar cambios de estado")],
    )


def fixture_guide() -> ActivityGuide:
    return ActivityGuide(
        title="Guía", overview="Exploración guiada", targeted_learning_objectives=[OBJECTIVE],
        activities=[ClassroomActivity(id="act-1", stage_name="Desarrollo", title="Observación de hielo", duration_minutes=20, grouping="grupos", purpose="Explorar", teacher_instructions=["Observar hielo."], expected_student_output="Registro de observación.", materials=["Hielo"], differentiation=ActivityDifferentiation(support="Imagen.", extension="Explicar."))],
        materials_summary=["Hielo"],
    )


def fixture_assessment(item_text: str) -> Assessment:
    item = AssessmentItem(id="item-1", type="respuesta breve", question=item_text, expected_answer="Explica el cambio de estado.", points=2, learning_objective=OBJECTIVE, cognitive_level="comprender")
    return Assessment(title="Salida", instructions=["Responde."], suggested_application_minutes=5, total_points=2, items=[item], specification_table=[SpecificationRow(learning_objective=OBJECTIVE, item_count=1, item_ids=["item-1"], total_points=2, cognitive_levels=["comprender"])], rubric=[RubricCriterion(criterion="Explicación", item_ids=["item-1"], levels=RubricLevels(logrado="Explica el cambio.", en_proceso="Explica parcialmente.", requiere_apoyo="No lo explica."))])


class FakePlanner:
    async def run(self, context): return fixture_plan()


class FakeDesigner:
    async def run(self, context, plan, repair_notes=""): return fixture_guide()


class FakeAssessment:
    calls: list[str] = []
    async def run(self, context, plan, guide, repair_notes=""):
        self.calls.append(repair_notes)
        if repair_notes:
            return fixture_assessment("Explica por qué el hielo observado se derrite.")
        return fixture_assessment("Según la estación final, ¿qué midieron en la cubetera?")


class FakeReviewer:
    calls = 0
    async def run(self, context, plan, guide, assessment):
        self.__class__.calls += 1
        if self.__class__.calls == 1:
            finding = ReviewFinding(id="rev-1", severity="bloqueante", responsible_agent="assessment", category="grounding", artifact_type="assessment_item", artifact_id="item-1", description="La estación final no existe en la guía.", suggested_correction="Eliminar la estación final y usar la observación de hielo.")
            return ReviewReport(status="findings_remaining", summary="Hallazgo de grounding.", findings=[finding])
        return ReviewReport(status="clean", summary="Pack coherente.", findings=[])


class ReviewCorrectionTest(unittest.IsolatedAsyncioTestCase):
    async def test_blocking_assessment_finding_triggers_targeted_repair(self):
        from app.services import generation
        FakeAssessment.calls = []
        FakeReviewer.calls = 0
        request = LessonRequest(description="Clase de ciencias sobre cambios de estado del agua.")
        with patch.object(generation, "PlannerAgent", FakePlanner), patch.object(generation, "DesignerAgent", FakeDesigner), patch.object(generation, "AssessmentAgent", FakeAssessment), patch.object(generation, "ReviewerAgent", FakeReviewer):
            frames = [frame async for frame in generation.generate_teaching_pack_events(request)]
        events = [(frame.split("\n", 1)[0].removeprefix("event: "), json.loads(frame.split("data: ", 1)[1])) for frame in frames]
        names = [name for name, _ in events]
        self.assertIn("reviewer_correcting", names)
        self.assertEqual(names.count("reviewer_started"), 1)
        self.assertEqual(FakeReviewer.calls, 2)
        self.assertEqual(len(FakeAssessment.calls), 2)
        self.assertIn("item-1", FakeAssessment.calls[1])
        self.assertIn("estación final", FakeAssessment.calls[1])
        report = next(data["review"] for name, data in events if name == "reviewer_completed")
        self.assertTrue(report["correction"]["attempted"])
        self.assertEqual(report["correction"]["target_agent"], "assessment")
        self.assertEqual(report["correction"]["outcome"], "corrected")


if __name__ == "__main__":
    unittest.main()
