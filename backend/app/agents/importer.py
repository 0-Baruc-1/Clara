import json
from openai import OpenAIError
from pydantic import ValidationError
from app.agents.base import AgentContext
from app.core.config import settings
from app.core.openai_client import SHARED_SYSTEM_CONTEXT, parse_structured_response
from app.models.teaching_pack import ImportedAuditBundle

class ImportGenerationError(RuntimeError): pass

class ImporterAgent:
    async def run(self, context: AgentContext, content: str, declared_kind: str) -> ImportedAuditBundle:
        prompt = f"""Interpreta material docente externo en español sin mejorarlo ni inventar contenido. Extrae sólo lo que aparece. Para OA citados, conserva código y texto como afirmaciones observadas; usa source='Declarado en el material importado' y status='partial'. Si una sección no puede leerse con fiabilidad, déjala ausente, baja su confianza y agrega una ParseNote con un extracto. Material declarado como: {declared_kind}. Referencia opcional proporcionada por quien audita: asignatura={context.request.subject or 'no indicada'}, nivel={context.request.grade_level or 'no indicado'}; úsala sólo para interpretar el contexto, nunca para inventar contenido.
MATERIAL:
{content}"""
        try:
            parsed = await parse_structured_response(model=settings.openai_model, system_context=f"{context.system_context or SHARED_SYSTEM_CONTEXT}\nEres el importador conservador de Clara.", user_prompt=prompt, response_format=ImportedAuditBundle)
            if parsed is None: raise ValueError("Sin salida estructurada")
            return parsed
        except (OpenAIError, ValidationError, ValueError) as error:
            raise ImportGenerationError("No fue posible interpretar el material con suficiente claridad para auditarlo.") from error
