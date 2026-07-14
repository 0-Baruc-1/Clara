from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SpanishModel(BaseModel):
    """All public teaching-pack schemas reject unexpected model fields."""

    model_config = ConfigDict(extra="forbid")


class CurriculumObjective(SpanishModel):
    code: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source: str = Field(min_length=1)


class CurriculumAlignment(SpanishModel):
    status: Literal["aligned", "partial", "not_found"]
    notes: list[str] = Field(default_factory=list)
    objectives: list[CurriculumObjective] = Field(default_factory=list)


class LessonStage(SpanishModel):
    name: str = Field(min_length=1)
    duration_minutes: int = Field(ge=1, le=480)
    purpose: str = Field(min_length=1)
    teacher_actions: list[str] = Field(min_length=1)
    student_actions: list[str] = Field(min_length=1)
    formative_check: str | None = None

class LessonPlan(SpanishModel):
    title: str
    subject: str
    grade_level: str
    duration_minutes: int = Field(ge=1, le=480)
    curriculum_alignment: CurriculumAlignment
    learning_objectives: list[str]
    key_concepts: list[str]
    prerequisite_knowledge: list[str]
    materials: list[str]
    stages: list[LessonStage] = Field(min_length=1)

class ActivityGuide(SpanishModel):
    title: str
    materials: list[str]
    instructions: list[str]

class RubricCriterion(SpanishModel):
    criterion: str
    achieved: str
    developing: str
    beginning: str

class Assessment(SpanishModel):
    title: str
    instructions: list[str]
    rubric: list[RubricCriterion]

class TeachingPack(SpanishModel):
    lesson_plan: LessonPlan
    activities: ActivityGuide
    assessment: Assessment
    review_notes: list[str] = Field(default_factory=list)
