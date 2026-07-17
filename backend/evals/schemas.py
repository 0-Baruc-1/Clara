"""Contracts for hand-authored Reviewer evaluation cases."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


ErrorClass = Literal[
    "declared_oa_not_worked",
    "item_not_assessing_claimed_oa",
    "incorrect_arithmetic_answer",
    "activity_material_gap",
    "fabricated_oa",
    "grounding_absent_experiment",
]
ArtifactType = Literal["plan", "activity", "assessment_item", "rubric", "material"]
FindingCategory = Literal[
    "grounding",
    "objective_coherence",
    "pedagogical_coherence",
    "curriculum_honesty",
    "internal_contradiction",
    "coverage",
]
ResponsibleAgent = Literal["planner", "designer", "assessment", "materials"]
Severity = Literal["bloqueante", "importante", "menor"]
FindingOrigin = Literal["model", "host_enforced"]


@dataclass(frozen=True)
class ArtifactAnchor:
    artifact_type: ArtifactType
    artifact_id: str


@dataclass(frozen=True)
class MaterialMutation:
    """A hand-authored change applied to a named baseline in milestone 2."""

    path: str
    operation: Literal["replace", "append", "remove"]
    value: object
    explanation: str


@dataclass(frozen=True)
class InjectedError:
    id: str
    error_class: ErrorClass
    target: ArtifactAnchor
    explanation: str


@dataclass(frozen=True)
class ExpectedFinding:
    """Strict detection contract; severity is assessed separately from detection."""

    issue_id: str
    error_class: ErrorClass
    action: Literal["emit", "suppress"]
    category: FindingCategory
    target: ArtifactAnchor
    responsible_agent: ResponsibleAgent
    minimum_severity: Severity
    detection_origin: FindingOrigin = "model"


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    title: str
    provenance: Literal["synthetic", "captured"]
    kind: Literal["error", "control", "audit_gate"]
    baseline_id: str
    material_mutations: tuple[MaterialMutation, ...] = ()
    injected_errors: tuple[InjectedError, ...] = ()
    expected: tuple[ExpectedFinding, ...] = ()
    activity_confidence: Literal["alta", "media", "baja"] = "alta"
    assessment_confidence: Literal["alta", "media", "baja"] = "alta"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ObservedFinding:
    """Minimal projection of a real ReviewFinding for matching and reports."""

    id: str
    severity: Severity
    responsible_agent: ResponsibleAgent
    category: FindingCategory
    artifact_type: ArtifactType
    artifact_id: str
    description: str = ""
    origin: FindingOrigin = "model"


@dataclass(frozen=True)
class MatchedFinding:
    expected_issue_id: str
    observed_id: str
    severity_correct: bool
    origin: FindingOrigin


@dataclass(frozen=True)
class NearMiss:
    expected_issue_id: str
    observed_id: str
    expected_agent: ResponsibleAgent
    observed_agent: ResponsibleAgent


@dataclass
class MatchResult:
    case_id: str
    matches: list[MatchedFinding] = field(default_factory=list)
    false_negatives: list[ExpectedFinding] = field(default_factory=list)
    false_positives: list[ObservedFinding] = field(default_factory=list)
    near_misses: list[NearMiss] = field(default_factory=list)
    correctly_suppressed: list[ExpectedFinding] = field(default_factory=list)
    suppression_violations: list[tuple[ExpectedFinding, ObservedFinding]] = field(default_factory=list)
