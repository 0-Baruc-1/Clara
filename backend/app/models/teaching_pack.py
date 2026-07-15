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

class ActivityDifferentiation(SpanishModel):
    support: str = Field(min_length=1)
    extension: str = Field(min_length=1)


class ClassroomActivity(SpanishModel):
    id: str = Field(min_length=1)
    stage_name: str = Field(min_length=1)
    title: str = Field(min_length=1)
    duration_minutes: int = Field(ge=1, le=480)
    grouping: Literal["individual", "parejas", "grupos", "curso completo"]
    purpose: str = Field(min_length=1)
    teacher_instructions: list[str] = Field(min_length=1)
    expected_student_output: str = Field(min_length=1)
    materials: list[str] = Field(default_factory=list)
    differentiation: ActivityDifferentiation


class ActivityGuide(SpanishModel):
    title: str = Field(min_length=1)
    overview: str = Field(min_length=1)
    targeted_learning_objectives: list[str] = Field(min_length=1)
    activities: list[ClassroomActivity] = Field(min_length=1)
    materials_summary: list[str] = Field(default_factory=list)


class ActivityGuideDraft(SpanishModel):
    """Structured model response; material summary is derived in application code."""

    title: str = Field(min_length=1)
    overview: str = Field(min_length=1)
    targeted_learning_objectives: list[str] = Field(min_length=1)
    activities: list[ClassroomActivity] = Field(min_length=1)

class AssessmentOption(SpanishModel):
    label: str = Field(min_length=1)
    text: str = Field(min_length=1)


class AssessmentItem(SpanishModel):
    id: str = Field(min_length=1)
    type: Literal["selección múltiple", "respuesta breve", "desarrollo"]
    question: str = Field(min_length=1)
    options: list[AssessmentOption] = Field(default_factory=list)
    correct_option_label: str | None = None
    expected_answer: str = Field(min_length=1)
    points: int = Field(ge=1)
    learning_objective: str = Field(min_length=1)
    cognitive_level: Literal["recordar", "comprender", "aplicar", "analizar"]


class RubricLevels(SpanishModel):
    logrado: str = Field(min_length=1)
    en_proceso: str = Field(min_length=1)
    requiere_apoyo: str = Field(min_length=1)


class RubricCriterion(SpanishModel):
    criterion: str = Field(min_length=1)
    item_ids: list[str] = Field(min_length=1)
    levels: RubricLevels


class SpecificationRow(SpanishModel):
    learning_objective: str
    item_count: int
    item_ids: list[str]
    total_points: int
    cognitive_levels: list[Literal["recordar", "comprender", "aplicar", "analizar"]]


class Assessment(SpanishModel):
    title: str = Field(min_length=1)
    instructions: list[str] = Field(min_length=1)
    suggested_application_minutes: int = Field(ge=1, le=480)
    total_points: int = Field(ge=1)
    specification_table: list[SpecificationRow] = Field(min_length=1)
    items: list[AssessmentItem] = Field(min_length=1)
    rubric: list[RubricCriterion] = Field(min_length=1)


class AssessmentDraft(SpanishModel):
    title: str
    instructions: list[str] = Field(min_length=1)
    suggested_application_minutes: int = Field(ge=1, le=480)
    total_points: int = Field(ge=1)
    items: list[AssessmentItem] = Field(min_length=1)
    rubric: list[RubricCriterion] = Field(min_length=1)

class ReviewFinding(SpanishModel):
    id: str
    severity: Literal["bloqueante", "importante", "menor"]
    responsible_agent: Literal["planner", "designer", "assessment"]
    category: Literal["grounding", "objective_coherence", "pedagogical_coherence", "curriculum_honesty", "internal_contradiction"]
    artifact_type: Literal["plan", "activity", "assessment_item", "rubric"]
    artifact_id: str
    description: str
    suggested_correction: str
class ReviewCorrection(SpanishModel):
    attempted: bool = False
    target_agent: Literal["designer", "assessment"] | None = None
    outcome: Literal["corrected", "findings_remaining", "regeneration_failed"] | None = None
class ReviewReport(SpanishModel):
    status: Literal["clean", "findings_remaining"]
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    correction: ReviewCorrection = Field(default_factory=ReviewCorrection)
class ReviewReportDraft(SpanishModel):
    status: Literal["clean", "findings_remaining"]
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)

class TeachingPack(SpanishModel):
    lesson_plan: LessonPlan
    activities: ActivityGuide
    assessment: Assessment
    review_notes: list[str] = Field(default_factory=list)
