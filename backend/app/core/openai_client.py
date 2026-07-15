"""OpenAI wiring and the shared prompt-caching seam."""
import json
from collections.abc import Callable
from typing import Any, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel
from app.core.config import settings

SHARED_SYSTEM_CONTEXT = """Eres Clara, un copiloto pedagógico para docentes de Chile.
TODO: Añadir instrucciones compartidas y contexto curricular chileno validado.
"""
OutputT = TypeVar("OutputT", bound=BaseModel)

def get_openai_client() -> AsyncOpenAI:
    if not settings.openai_api_key: raise RuntimeError("OPENAI_API_KEY no está configurada.")
    return AsyncOpenAI(api_key=settings.openai_api_key)

async def parse_structured_response(*, model: str, system_context: str, user_prompt: str, response_format: type[OutputT]) -> OutputT | None:
    response = await get_openai_client().responses.parse(model=model, input=[{"role":"system","content":system_context},{"role":"user","content":user_prompt}], text_format=response_format)
    return None if response.output_parsed is None else response_format.model_validate(response.output_parsed)

async def parse_structured_response_with_tools(*, model: str, system_context: str, user_prompt: str, response_format: type[OutputT], tools: list[dict[str, Any]], tool_handler: Callable[[str, dict[str, Any]], dict[str, Any]]) -> OutputT:
    """Function loop using SDK parse: Pydantic owns strict-schema conversion."""
    client = get_openai_client()
    response = await client.responses.parse(model=model, input=[{"role":"system","content":system_context},{"role":"user","content":user_prompt}], tools=tools, text_format=response_format)
    for _ in range(8):
        calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
        if not calls:
            if response.output_parsed is None: raise ValueError("El modelo no devolvió una salida estructurada después de usar herramientas.")
            return response_format.model_validate(response.output_parsed)
        outputs = [{"type":"function_call_output", "call_id":call.call_id, "output":json.dumps(tool_handler(call.name, json.loads(call.arguments)), ensure_ascii=False)} for call in calls]
        response = await client.responses.parse(model=model, previous_response_id=response.id, input=outputs, tools=tools, text_format=response_format)
    raise RuntimeError("El agente excedió el límite de consultas curriculares.")
