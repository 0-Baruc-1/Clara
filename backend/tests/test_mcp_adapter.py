import unittest
from unittest.mock import patch

from app.mcp_server import auditar_material_educativo, buscar_objetivos, verificar_objetivo
from app.models.teaching_pack import AuditReport, ReviewFinding


class McpAdapterTests(unittest.IsolatedAsyncioTestCase):
    def test_verification_is_unambiguous_for_an_invalid_oa(self):
        result = verificar_objetivo("CN06 OA 999")
        self.assertFalse(result["existe"])
        self.assertIsNone(result["objetivo"])
        self.assertIn("No cites", result["accion_recomendada"])

    def test_objective_search_uses_the_existing_provider(self):
        result = buscar_objetivos("Ciencias Naturales", "6° básico", "cambios de estado del agua")
        self.assertTrue(result["cobertura_encontrada"])
        self.assertIn("CN06 OA 13", [item["objective"]["code"] for item in result["objetivos"]])

    async def test_audit_tool_delegates_to_existing_audit_service(self):
        report = AuditReport(
            overall_status="requiere_atencion", source_summary="Material leído.", parse_confidence="alta",
            findings=[ReviewFinding(id="oa", severity="bloqueante", responsible_agent="planner", category="curriculum_honesty", artifact_type="plan", artifact_id="CN06 OA 999", description="No existe.", suggested_correction="Reemplázalo.")],
        )
        with patch("app.mcp_server.audit_material_report", return_value=report) as audit:
            result = await auditar_material_educativo("Plan de ciencias con un objetivo declarado para una clase.", "Ciencias Naturales", "6° básico")
        audit.assert_awaited_once()
        self.assertEqual(result["findings"][0]["artifact_id"], "CN06 OA 999")
        self.assertEqual(result["findings"][0]["severity"], "bloqueante")


if __name__ == "__main__":
    unittest.main()
