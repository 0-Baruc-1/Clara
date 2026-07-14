"""OpenAI wiring and the shared prompt-caching seam."""
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel
from app.core.config import settings

# Stable prefix: keep first in future agent requests for prompt-cache reuse.
SHARED_SYSTEM_CONTEXT = """Eres Clara, un copiloto pedagógico para docentes de Chile.
TODO: Añadir instrucciones compartidas y contexto curricular chileno validado.
"""

OutputT = TypeVar("OutputT", bound=BaseModel)

def get_openai_client() -> AsyncOpenAI:
    """Build the SDK client lazily; no network call occurs here."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurada.")
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def parse_structured_response(
    *,
    model: str,
    system_context: str,
    user_prompt: str,
    response_format: type[OutputT],
) -> OutputT | None:
    """Request a Pydantic-validated Responses API output with a chosen model.

    ``system_context`` must begin with stable shared content. Keeping it before
    variable request data preserves the exact-prefix shape needed for caching.
    """
    client = get_openai_client()
    response = await client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_prompt},
        ],
        text_format=response_format,
    )
    parsed = response.output_parsed
    return None if parsed is None else response_format.model_validate(parsed)
