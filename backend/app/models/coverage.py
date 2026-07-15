from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.teaching_pack import ReviewFinding, SpanishModel


class CoverageObjective(SpanishModel):
    code: str
    description: str
    coverage_count: int = Field(ge=0)
    declared_unverified_count: int = Field(ge=0)
    declared_without_activity_evidence_count: int = Field(ge=0)
    pack_dates: list[datetime] = Field(default_factory=list)
    status: Literal["trabajado", "aun_no_visto"]


class CoverageOverview(SpanishModel):
    subject: str
    grade_level: str
    reviewed_pack_count: int = Field(ge=0)
    scope_note: str
    objectives: list[CoverageObjective] = Field(default_factory=list)
    longitudinal_findings: list[ReviewFinding] = Field(default_factory=list)
