"""Production Reviewer adapter for evaluation runs (never used by mock mode)."""
from __future__ import annotations

from app.agents.base import AgentContext
from app.agents.reviewer import ReviewerAgent
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT
from app.models.requests import LessonRequest

from .cases import EvaluationCase
from .material_factory import build_case_material
from .schemas import ObservedFinding


class ProductionReviewerAdapter:
    """Calls the unmodified Reviewer on hand-authored, typed evaluation fixtures."""

    async def run(self, case: EvaluationCase) -> list[ObservedFinding]:
        plan, activities, assessment = build_case_material(case)
        context = AgentContext(
            request=LessonRequest(
                description=f"Evaluación interna del Reviewer: {case.id}",
                subject=plan.subject,
                grade_level=plan.grade_level,
                duration_minutes=plan.duration_minutes,
            ),
            system_context=SHARED_SYSTEM_CONTEXT,
            model=settings.reviewer_model or settings.openai_model,
        )
        reviewer = ReviewerAgent()
        report = await reviewer.run(context, plan, activities, assessment, teacher_edit_mode=True)
        invalid_codes = {
            call["arguments"]["codigo"].casefold()
            for call in reviewer.tool_trace
            if call["tool"] == "verificar_objetivo" and not call["result"].get("existe", True)
        }
        findings: list[ObservedFinding] = []
        for finding in report.findings:
            # The Reviewer itself appends these deterministic findings after tool verification.
            origin = "host_enforced" if finding.id == f"oa-{finding.artifact_id}" and finding.artifact_id.casefold() in invalid_codes else "model"
            findings.append(ObservedFinding(
                id=finding.id,
                severity=finding.severity,
                responsible_agent=finding.responsible_agent,
                category=finding.category,
                artifact_type=finding.artifact_type,
                artifact_id=finding.artifact_id,
                description=finding.description,
                origin=origin,
            ))
        return findings
