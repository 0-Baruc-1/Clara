from pydantic import BaseModel, ConfigDict, Field

from app.models.teaching_pack import CurriculumObjective


class CurriculumEntry(BaseModel):
    """A verified curriculum objective supplied from a local data source."""

    model_config = ConfigDict(extra="forbid")
    subject: str
    grade_level: str
    objective: CurriculumObjective
    keywords: list[str] = Field(default_factory=list)


class CurriculumCatalog(BaseModel):
    source_name: str
    entries: list[CurriculumEntry]
