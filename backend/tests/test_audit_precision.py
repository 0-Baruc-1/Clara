import unittest
from unittest.mock import patch
from app.models.teaching_pack import ReviewFinding
from app.curriculum.tools import CurriculumToolFailure
from app.models.requests import AuditRequest
from app.services.audit import audit_material_events, conservative_findings

def finding(category: str) -> ReviewFinding:
    return ReviewFinding(id=category, severity="bloqueante", responsible_agent="planner", category=category, artifact_type="plan", artifact_id="x", description="x", suggested_correction="x")

class AuditPrecisionTests(unittest.TestCase):
    def test_low_confidence_suppresses_absence_claims_but_keeps_invalid_oa(self):
        findings = conservative_findings([finding("objective_coherence"), finding("grounding"), finding("curriculum_honesty")], "baja", "media")
        self.assertEqual([item.category for item in findings], ["curriculum_honesty"])


class AuditErrorHandlingTests(unittest.IsolatedAsyncioTestCase):
    async def test_curriculum_failure_is_streamed_without_a_stack_trace(self):
        class FailingImporter:
            async def run(self, *_args):
                raise CurriculumToolFailure("La fuente curricular no está disponible; no es seguro continuar sin verificar OA.")

        with patch("app.services.audit.ImporterAgent", FailingImporter):
            frames = [
                frame
                async for frame in audit_material_events(
                    AuditRequest(content="Planificación suficientemente extensa para activar la auditoría.")
                )
            ]
        self.assertEqual(frames[-1].split("\n", 1)[0], "event: audit_failure")
        self.assertIn("fuente curricular", frames[-1])
