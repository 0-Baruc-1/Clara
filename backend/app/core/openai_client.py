"""OpenAI wiring and the shared prompt-caching seam."""
import json
from collections.abc import Callable
from typing import Any, TypeVar

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from app.core.config import settings


SHARED_SYSTEM_CONTEXT = """Eres Clara, una capa de planificación y verificación pedagógica para docentes de Chile.

Todo contenido destinado a docentes debe estar en español claro, respetuoso y accionable. Diseña para el nivel y la duración solicitados; distingue entre el arco de la clase, las actividades, la evaluación y los materiales imprimibles. No presentes una inferencia como un hecho ni inventes experiencias, evidencias, códigos OA o referencias curriculares.

La fuente curricular es externa y verificable: cuando tengas herramientas curriculares disponibles, úsalas antes de citar un OA y trata su resultado como la única evidencia de validez. Si la fuente no puede consultarse, falla de forma segura; no sustituyas la verificación con memoria. Al auditar material externo o cambios docentes, formula hallazgos de ausencia como observaciones sobre lo que pudiste leer, nunca como un juicio sobre la docente.

Mantén la trazabilidad entre objetivos, actividades, evaluación y materiales. Prefiere datos estructurados, descriptores observables y correcciones concretas; conserva lo ya correcto cuando recibas una corrección focalizada.
"""

OutputT = TypeVar("OutputT", bound=BaseModel)


class OpenAIRequestError(RuntimeError):
    """Safe, teacher-facing OpenAI error that never includes credentials."""

    def __init__(self, message: str, *, error_type: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        # Internal diagnostics may inspect only these non-secret transport facts.
        self.error_type = error_type
        self.status_code = status_code


def _safe_openai_message(error: OpenAIError) -> str:
    status_code = getattr(error, "status_code", None)
    if status_code in {401, 403} or error.__class__.__name__ == "AuthenticationError":
        return "OpenAI no aceptó la clave proporcionada. Revísala e inténtalo nuevamente."
    return "No fue posible completar la consulta a OpenAI. Inténtalo nuevamente."


def get_openai_client(api_key: str | None = None) -> AsyncOpenAI:
    key = api_key or settings.openai_api_key
    if not key:
        raise OpenAIRequestError("No hay una clave de OpenAI disponible para esta solicitud.")
    return AsyncOpenAI(api_key=key)


async def parse_structured_response(
    *,
    model: str,
    system_context: str,
    user_prompt: str,
    response_format: type[OutputT],
    api_key: str | None = None,
) -> OutputT | None:
    try:
        response = await get_openai_client(api_key).responses.parse(
            model=model,
            input=[{"role": "system", "content": system_context}, {"role": "user", "content": user_prompt}],
            text_format=response_format,
        )
        return None if response.output_parsed is None else response_format.model_validate(response.output_parsed)
    except OpenAIError as error:
        raise OpenAIRequestError(
            _safe_openai_message(error),
            error_type=type(error).__name__,
            status_code=getattr(error, "status_code", None),
        ) from None


async def parse_structured_response_with_tools(
    *,
    model: str,
    system_context: str,
    user_prompt: str,
    response_format: type[OutputT],
    tools: list[dict[str, Any]],
    tool_handler: Callable[[str, dict[str, Any]], dict[str, Any]],
    api_key: str | None = None,
) -> OutputT:
    """Function loop using SDK parse: Pydantic owns strict-schema conversion."""
    try:
        client = get_openai_client(api_key)
        response = await client.responses.parse(
            model=model,
            input=[{"role": "system", "content": system_context}, {"role": "user", "content": user_prompt}],
            tools=tools,
            text_format=response_format,
        )
        for _ in range(8):
            calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
            if not calls:
                if response.output_parsed is None:
                    raise ValueError("El modelo no devolvió una salida estructurada después de usar herramientas.")
                return response_format.model_validate(response.output_parsed)
            outputs = [
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(tool_handler(call.name, json.loads(call.arguments)), ensure_ascii=False),
                }
                for call in calls
            ]
            response = await client.responses.parse(
                model=model,
                previous_response_id=response.id,
                input=outputs,
                tools=tools,
                text_format=response_format,
            )
        raise RuntimeError("El agente excedió el límite de consultas curriculares.")
    except OpenAIError as error:
        raise OpenAIRequestError(
            _safe_openai_message(error),
            error_type=type(error).__name__,
            status_code=getattr(error, "status_code", None),
        ) from None
