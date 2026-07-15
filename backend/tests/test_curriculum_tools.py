import unittest
from app.curriculum.provider import JsonCurriculumProvider
from app.curriculum.tools import curriculum_tool_handler

class CurriculumToolTests(unittest.TestCase):
    def setUp(self): self.handler = curriculum_tool_handler(JsonCurriculumProvider(), [])
    def test_water_topic_returns_expected_objectives(self):
        result = self.handler("buscar_objetivos", {"asignatura":"Ciencias Naturales", "nivel":"6\u00b0 b\u00e1sico", "tema":"cambios de estado del agua"})
        self.assertTrue(result["cobertura_encontrada"])
        self.assertTrue({"CN06 OA 13", "CN06 OA 15"}.issubset({item["objective"]["code"] for item in result["objetivos"]}))
    def test_level_variants_keep_coverage(self):
        for level in ("6 b\u00e1sico", "6 basico", "6\u00b0 basico", "6\u00ba b\u00e1sico"):
            result = self.handler("buscar_objetivos", {"asignatura":"Ciencias Naturales", "nivel":level, "tema":None})
            self.assertIn("CN06 OA 13", {item["objective"]["code"] for item in result["objetivos"]}, level)
