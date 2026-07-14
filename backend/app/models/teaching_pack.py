from pydantic import BaseModel, Field

class LessonPlan(BaseModel):
    title: str
    learning_objectives: list[str]
    duration_minutes: int
    sequence: list[str]

class ActivityGuide(BaseModel):
    title: str
    materials: list[str]
    instructions: list[str]

class RubricCriterion(BaseModel):
    criterion: str
    achieved: str
    developing: str
    beginning: str

class Assessment(BaseModel):
    title: str
    instructions: list[str]
    rubric: list[RubricCriterion]

class TeachingPack(BaseModel):
    lesson_plan: LessonPlan
    activities: ActivityGuide
    assessment: Assessment
    review_notes: list[str] = Field(default_factory=list)

