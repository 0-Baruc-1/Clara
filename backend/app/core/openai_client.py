"""OpenAI wiring and the shared prompt-caching seam."""
from openai import AsyncOpenAI
from app.core.config import settings

# Stable prefix: keep first in future agent requests for prompt-cache reuse.
SHARED_SYSTEM_CONTEXT = """Eres Clara, un copiloto pedagógico para docentes de Chile.
TODO: Añadir instrucciones compartidas y contexto curricular chileno validado.
"""

def get_openai_client() -> AsyncOpenAI:
    """Build the SDK client lazily; no network call occurs here."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY no está configurada.")
    return AsyncOpenAI(api_key=settings.openai_api_key)

