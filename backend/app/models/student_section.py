"""Typed contracts for teacher-attested student practice.

These models intentionally contain no mastery field.  A response is evidence to
inspect; only the teacher may interpret it in the context of the student.
"""
from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudentSectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeterministicValidatorCandidate(StudentSectionModel):
    """A candidate only. The host validates it before it can become executable."""

    kind: Literal["sympy_equivalence"]
    expected_expression: str = Field(min_length=1, max_length=128)
    allowed_symbols: list[Literal["x"]] = Field(default_factory=list)


class PracticeItemForPublication(StudentSectionModel):
    source_assessment_item_id: str | None = Field(default=None, max_length=200)
    ordinal: int = Field(ge=1, le=100)
    item_snapshot: dict[str, Any]
    # This is an observed label from the source. It may be removed at publish
    # time if the host cannot verify it; the item itself remains usable.
    requested_evidence_objective_code: str | None = Field(default=None, max_length=80)
    deterministic_validator_candidate: DeterministicValidatorCandidate | None = None


class PublishPracticeMaterialRequest(StudentSectionModel):
    class_id: UUID
    source_pack_reference: str = Field(min_length=1, max_length=200)
    source_pack_version_reference: str | None = Field(default=None, max_length=200)
    source_review_reference: str | None = Field(default=None, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    content_snapshot: dict[str, Any]
    # A source-pack claim remains a claim; it never becomes student evidence by
    # itself. Keeping it separate makes the two lanes queryable without merging.
    declared_objective_codes: list[str] = Field(default_factory=list, max_length=60)
    attestation_statement_version: str = Field(min_length=1, max_length=100)
    items: list[PracticeItemForPublication] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_ordinals(self) -> "PublishPracticeMaterialRequest":
        if len({item.ordinal for item in self.items}) != len(self.items):
            raise ValueError("Cada ítem publicado debe tener un orden único.")
        return self


class PublicationObjectiveAttestation(StudentSectionModel):
    objective_code: str
    official_wording_snapshot: str
    curriculum_source_url: str
    verification_run_id: str


class PreparedPracticeItem(StudentSectionModel):
    source_assessment_item_id: str | None = None
    ordinal: int
    item_snapshot: dict[str, Any]
    evidence_objective_code: str | None = None
    evidence_exclusion_reason: Literal["oa_no_verificable", "sin_etiqueta_oa"] | None = None
    validation_mode: Literal["deterministic", "teacher_judgment"]
    deterministic_validator: dict[str, Any] | None = None


class PreparedPublication(StudentSectionModel):
    source_pack_reference: str
    source_pack_version_reference: str | None = None
    source_review_reference: str | None = None
    title: str
    content_snapshot: dict[str, Any]
    declared_objective_codes: list[str] = Field(default_factory=list)
    attestation_statement_version: str
    objectives: list[PublicationObjectiveAttestation] = Field(default_factory=list)
    items: list[PreparedPracticeItem] = Field(min_length=1)


class PublishPracticeMaterialResponse(StudentSectionModel):
    publication_version_id: UUID
    # This is the student-facing immutable release created when its publication
    # version transitions to ``published``.  Keeping both IDs explicit avoids
    # asking a client to infer a relation that is intentionally database-owned.
    release_id: UUID
    published_item_count: int
    attested_objective_codes: list[str]
    practice_only_item_count: int
    note: str


class StudentResponseRequest(StudentSectionModel):
    answer: str = Field(min_length=1, max_length=2000)


class StudentResponseReceipt(StudentSectionModel):
    response_attempt_id: UUID
    feedback_state: Literal["verified", "not_applicable", "unavailable"]
    feedback_message: str


class StudentPracticeItem(StudentSectionModel):
    id: UUID
    ordinal: int
    item_snapshot: dict[str, Any]
    evidence_objective_code: str | None = None
    validation_mode: Literal["deterministic", "teacher_judgment"]


class StudentPracticeMaterial(StudentSectionModel):
    release_id: UUID
    publication_version_id: UUID
    title: str
    items: list[StudentPracticeItem]


class StudentMaterialRelease(StudentSectionModel):
    """Non-content metadata a student may discover through RLS."""

    release_id: UUID
    title: str
    released_at: str


class StudentObjectiveEvidence(StudentSectionModel):
    student_id: UUID
    student_full_name: str | None = None
    objective_code: str
    # A declared OA is a source-pack claim. It is deliberately separate from
    # host-verified teacher attestation and from student response evidence.
    declared_publication_count: int
    attested_item_count: int
    distinct_items_responded: int
    evidence_threshold: int
    state: Literal["evidencia_suficiente", "evidencia_insuficiente"]
    wording: str
