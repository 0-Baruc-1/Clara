"""Generate only the printable classroom artifacts requested by activities."""
import json
from openai import OpenAIError
from pydantic import ValidationError
from app.agents.base import AgentContext
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT, parse_structured_response
from app.models.teaching_pack import ActivityGuide, MaterialCoverage, MaterialPack, MaterialPackDraft

PRINTABLE_HINTS = ("tabla", "tarjeta", "organizador", "hoja", "ficha", "ticket", "guía", "guia")
class MaterialsGenerationError(RuntimeError): pass

def requested_printables(guide: ActivityGuide) -> list[tuple[str, str]]:
    return [(a.id, label) for a in guide.activities for label in a.materials if any(hint in label.casefold() for hint in PRINTABLE_HINTS)]

class MaterialsAgent:
    max_attempts = 2
    async def run(self, context: AgentContext, guide: ActivityGuide, repair_notes: str = "") -> MaterialPack:
        requests = requested_printables(guide)
        prompt = f"""Genera solamente hojas imprimibles solicitadas explícitamente por estas actividades. Responde en español. No inventes materiales, experimentos, términos ni objetivos. Cada material debe copiar exactamente activity_id y source_material_label desde SOLICITUDES. El contenido debe ser una hoja lista para imprimir, usando bloques estructurados; no describas una hoja. Si una solicitud no puede resolverse, omítela: el sistema mostrará la brecha al docente.
SOLICITUDES={json.dumps(requests, ensure_ascii=False)}
ACTIVIDADES={json.dumps(guide.model_dump(mode='json'), ensure_ascii=False)}{repair_notes}"""
        error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                draft = await parse_structured_response(model=settings.materials_model or context.model or settings.openai_model, system_context=f"{context.system_context or SHARED_SYSTEM_CONTEXT}\nEres el agente de materiales imprimibles de Clara.", user_prompt=prompt, response_format=MaterialPackDraft, api_key=context.api_key)
                if draft is None: raise ValueError("El modelo no devolvió materiales estructurados.")
                return self._validate(draft, requests)
            except (OpenAIError, ValidationError, ValueError) as exc:
                error = exc
                if attempt == 0: prompt += f"\n\nCORRECCIÓN OBLIGATORIA: {exc}. Corrige exactamente este problema y conserva lo correcto."
        raise MaterialsGenerationError("No fue posible generar materiales imprimibles válidos. Intenta nuevamente.") from error
    @staticmethod
    def _validate(draft: MaterialPackDraft, requests: list[tuple[str, str]]) -> MaterialPack:
        allowed = {(activity_id, label.casefold()) for activity_id, label in requests}; seen: set[tuple[str, str]] = set()
        for material in draft.materials:
            key = (material.activity_id, material.source_material_label.casefold())
            if key not in allowed: raise ValueError(f"Material {material.id}: la referencia {material.activity_id}/{material.source_material_label!r} no existe en la actividad.")
            if key in seen: raise ValueError(f"Material {material.id}: duplica la solicitud {material.source_material_label!r}.")
            seen.add(key)
        coverage = [MaterialCoverage(activity_id=activity_id, source_material_label=label, fulfillment="material_generado", material_id=next(m.id for m in draft.materials if m.activity_id == activity_id and m.source_material_label.casefold() == label.casefold())) if (activity_id, label.casefold()) in seen else MaterialCoverage(activity_id=activity_id, source_material_label=label, fulfillment="sin_cobertura") for activity_id, label in requests]
        return MaterialPack(title=draft.title, materials=draft.materials, coverage=coverage)
