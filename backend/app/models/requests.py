from pydantic import BaseModel, Field
from typing import Literal
from app.models.teaching_pack import ActivityGuide, Assessment, LessonPlan, MaterialPack

class LessonRequest(BaseModel):
    description: str = Field(min_length=10, max_length=4000, description="Descripción libre de la clase.")
    subject: str | None = Field(default=None, max_length=100)
    grade_level: str | None = Field(default=None, max_length=100)
    topic: str | None = Field(default=None, max_length=300)
    duration_minutes: int | None = Field(default=None, ge=10, le=480)
    notes: str | None = Field(default=None, max_length=2000)
    teacher_session_id: str | None = Field(default=None, min_length=8, max_length=120)

class MaterialsRequest(BaseModel):
    lesson_plan: LessonPlan
    activities: ActivityGuide
    assessment: Assessment

class AuditRequest(BaseModel):
    content: str = Field(min_length=20, max_length=50000)
    declared_kind: Literal["auto", "lesson_plan", "assessment", "both"] = "auto"
    teacher_session_id: str | None = Field(default=None, min_length=8, max_length=120)


class EditedPackReviewRequest(BaseModel):
    """A teacher-edited pack is already structured, so it needs no importer pass."""

    lesson_plan: LessonPlan
    activities: ActivityGuide
    assessment: Assessment
    materials: MaterialPack | None = None
