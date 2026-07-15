import unittest
from app.models.teaching_pack import ReviewFinding
from app.services.audit import conservative_findings

def finding(category: str) -> ReviewFinding:
    return ReviewFinding(id=category, severity="bloqueante", responsible_agent="planner", category=category, artifact_type="plan", artifact_id="x", description="x", suggested_correction="x")

class AuditPrecisionTests(unittest.TestCase):
    def test_low_confidence_suppresses_absence_claims_but_keeps_invalid_oa(self):
        findings = conservative_findings([finding("objective_coherence"), finding("grounding"), finding("curriculum_honesty")], "baja", "media")
        self.assertEqual([item.category for item in findings], ["curriculum_honesty"])
