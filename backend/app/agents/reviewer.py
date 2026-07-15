import json
from openai import OpenAIError
from pydantic import ValidationError
from app.agents.base import AgentContext
from app.core.config import settings
from app.core.openai_client import parse_structured_response
from app.models.teaching_pack import ActivityGuide, Assessment, LessonPlan, MaterialPack, ReviewCorrection, ReviewReport, ReviewReportDraft

class ReviewerGenerationError(RuntimeError): pass

class ReviewerAgent:
    async def run(self, context: AgentContext, plan: LessonPlan, activities: ActivityGuide, assessment: Assessment, materials: MaterialPack | None = None) -> ReviewReport:
        materials_context = "" if materials is None else f"""\nMATERIALES={json.dumps(materials.model_dump(mode='json'), ensure_ascii=False)}
También audita que cada hoja pertenezca a la actividad que la solicita; que tarjetas usen sólo conceptos enseñados; que tablas y organizadores recojan el producto esperado; y que tickets correspondan a la verificación formativa. Toda cobertura con fulfillment='sin_cobertura' debe ser un hallazgo category='coverage', responsible_agent='materials', no bloqueante."""
        prompt = f"""Audita en español coherencia cruzada. Una pregunta puede aplicar un concepto a una situación cotidiana NUEVA, pero no puede afirmar que la clase observó, midió, registró, experimentó, usó una estación o tuvo evidencia de esa situación si no existe explícitamente en ACTIVIDADES. Trata evidencia inexistente como bloqueante de grounding y atribúyelo a assessment. Revisa también que suggested_application_minutes no exceda el tiempo de etapas de evaluación/evidencia del PLAN. No reescribas contenido. Devuelve hallazgos precisos con responsable, id y corrección.
PLAN={json.dumps(plan.model_dump(mode='json'), ensure_ascii=False)}
ACTIVIDADES={json.dumps(activities.model_dump(mode='json'), ensure_ascii=False)}
EVALUACION={json.dumps(assessment.model_dump(mode='json'), ensure_ascii=False)}{materials_context}"""
        try:
            out = await parse_structured_response(model=settings.reviewer_model or context.model or settings.openai_model, system_context=context.system_context, user_prompt=prompt, response_format=ReviewReportDraft)
            if out is None: raise ValueError("Sin informe")
            return ReviewReport(status=out.status, summary=out.summary, findings=out.findings, correction=ReviewCorrection())
        except (OpenAIError, ValidationError, ValueError) as error:
            raise ReviewerGenerationError("No fue posible revisar la coherencia del pack.") from error
