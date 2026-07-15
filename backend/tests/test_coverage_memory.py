import tempfile
import unittest
from pathlib import Path

from app.models.teaching_pack import CurriculumAlignment, CurriculumObjective, ReviewFinding, ReviewReport
from app.services.coverage import coverage_overview, record_reviewed_pack
from tests.test_review_correction import fixture_guide, fixture_plan


def plan_for(code: str):
    return fixture_plan().model_copy(update={
        "curriculum_alignment": CurriculumAlignment(status="aligned", objectives=[CurriculumObjective(code=code, description="Objetivo declarado.", source="Mineduc")]),
    })


def trace(code: str, exists: bool = True):
    return [{"tool": "verificar_objetivo", "arguments": {"codigo": code}, "result": {"existe": exists, "objetivo": {"description": "Objetivo oficial"} if exists else None}}]


class CoverageMemoryTests(unittest.TestCase):
    def test_only_verified_objectives_with_activity_evidence_count_as_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "coverage.sqlite3"
            session = "teacher-session-coverage"
            guide = fixture_guide()
            clean = ReviewReport(status="clean", summary="Correcto.")
            for _ in range(3):
                record_reviewed_pack(database_path=database, session_id=session, source_type="generated", plan=plan_for("CN06 OA 13"), activities=guide, review=clean, verification_trace=trace("CN06 OA 13"))
            missing_evidence = ReviewReport(status="findings_remaining", summary="Falta evidencia.", findings=[ReviewFinding(id="gap", severity="importante", responsible_agent="planner", category="objective_coherence", artifact_type="plan", artifact_id="CN06 OA 15", description="No hay evidencia.", suggested_correction="Añade actividad.")])
            record_reviewed_pack(database_path=database, session_id=session, source_type="generated", plan=plan_for("CN06 OA 15"), activities=guide, review=missing_evidence, verification_trace=trace("CN06 OA 15"))
            overview = coverage_overview(database_path=database, session_id=session, subject="Ciencias Naturales", grade_level="6° básico")

        objectives = {objective.code: objective for objective in overview.objectives}
        self.assertEqual(objectives["CN06 OA 13"].coverage_count, 3)
        self.assertEqual(objectives["CN06 OA 14"].coverage_count, 0)
        self.assertEqual(objectives["CN06 OA 15"].coverage_count, 0)
        self.assertEqual(objectives["CN06 OA 15"].declared_without_activity_evidence_count, 1)
        self.assertTrue(any(finding.artifact_id == "CN06 OA 14" for finding in overview.longitudinal_findings))


if __name__ == "__main__":
    unittest.main()
