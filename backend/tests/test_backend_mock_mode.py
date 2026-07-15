import asyncio
import json
import unittest

from app.core.config import settings
from app.fixtures.water_pack import water_assessment, water_guide, water_plan
from app.models.requests import AuditRequest, EditedPackReviewRequest, LessonRequest, MaterialsRequest
from app.services.audit import audit_material_events, review_edited_pack_events
from app.services.generation import generate_teaching_pack_events
from app.services.materials import generate_materials_events


class BackendMockModeTests(unittest.TestCase):
    def test_generation_fixture_never_needs_an_openai_key(self):
        previous = settings.mock_mode
        settings.mock_mode = True
        try:
            frames = asyncio.run(
                _collect(generate_teaching_pack_events(LessonRequest(description="Clase de ciencias sobre el agua.")))
            )
        finally:
            settings.mock_mode = previous
        events = [frame.split("\n", 1)[0].removeprefix("event: ") for frame in frames]
        completed = next(frame for frame in frames if frame.startswith("event: reviewer_completed"))
        payload = json.loads(next(line for line in completed.splitlines() if line.startswith("data: ")).removeprefix("data: "))
        self.assertIn("planner_completed", events)
        self.assertIn("reviewer_correcting", events)
        self.assertEqual(payload["review"]["correction"]["outcome"], "corrected")

    def test_every_model_backed_endpoint_has_an_offline_fixture_path(self):
        plan, guide, assessment = water_plan(), water_guide(), water_assessment()
        previous = settings.mock_mode
        settings.mock_mode = True
        try:
            materials = asyncio.run(_collect(generate_materials_events(MaterialsRequest(lesson_plan=plan, activities=guide, assessment=assessment))))
            audit = asyncio.run(_collect(audit_material_events(AuditRequest(content="Material de ejemplo suficientemente extenso para la auditoría."))))
            edits = asyncio.run(_collect(review_edited_pack_events(EditedPackReviewRequest(lesson_plan=plan, activities=guide, assessment=assessment))))
        finally:
            settings.mock_mode = previous
        self.assertTrue(materials[-1].startswith("event: materials_reviewer_completed"))
        self.assertTrue(audit[-1].startswith("event: audit_completed"))
        self.assertTrue(edits[-1].startswith("event: edited_review_completed"))


async def _collect(events):
    return [frame async for frame in events]
