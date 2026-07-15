"""Clara's thin MCP verification adapter: no generator tools, no duplicated audit logic."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.curriculum.provider import JsonCurriculumProvider
from app.curriculum.tools import CurriculumToolFailure, curriculum_tool_handler
from app.models.requests import AuditRequest
from app.services.audit import audit_material_report


clara_mcp = FastMCP(
    "Clara — Verificación curricular",
    instructions=(
        "Verifica material educativo chileno contra la fuente curricular de Clara. "
        "Usa auditar_material_educativo antes de entregar material a una docente cuando haga afirmaciones curriculares. "
        "Un objetivo cuenta como válido sólo si verificar_objetivo devuelve existe=true."
    ),
    json_response=True,
    stateless_http=True,
    streamable_http_path="/",
)


def _curriculum_call(name: str, arguments: dict[str, object]) -> dict[str, object]:
    trace: list[dict] = []
    try:
        return curriculum_tool_handler(JsonCurriculumProvider(), trace)(name, arguments)
    except CurriculumToolFailure as error:
        raise RuntimeError("La fuente curricular no está disponible; Clara no puede verificar este OA con seguridad.") from error


@clara_mcp.tool()
async def auditar_material_educativo(material: str, asignatura: str | None = None, nivel: str | None = None) -> dict[str, object]:
    """Audita un plan, guía o evaluación; devuelve hallazgos estructurados y conservadores en español."""
    if len(material.strip()) < 20:
        raise ValueError("El material debe tener al menos 20 caracteres para poder auditarlo.")
    report = await audit_material_report(AuditRequest(content=material, subject=asignatura, grade_level=nivel))
    return report.model_dump(mode="json")


@clara_mcp.tool()
def verificar_objetivo(codigo: str) -> dict[str, object]:
    """Verifica un OA contra la fuente curricular. existe=false significa que no debe citarse como OA oficial."""
    if not codigo.strip():
        raise ValueError("Debes proporcionar un código OA para verificar.")
    result = _curriculum_call("verificar_objetivo", {"codigo": codigo.strip()})
    if not result["existe"]:
        result["accion_recomendada"] = "No cites este código como OA oficial. Elimínalo o reemplázalo por un objetivo verificado."
    else:
        result["accion_recomendada"] = "Puedes usar este OA si corresponde a la asignatura, nivel y clase."
    return result


@clara_mcp.tool()
def buscar_objetivos(asignatura: str, nivel: str, tema: str | None = None) -> dict[str, object]:
    """Busca OA oficiales disponibles por asignatura, nivel y tema opcional, sin falsos vacíos por el tema."""
    if not asignatura.strip() or not nivel.strip():
        raise ValueError("Asignatura y nivel son obligatorios para buscar objetivos.")
    return _curriculum_call("buscar_objetivos", {"asignatura": asignatura.strip(), "nivel": nivel.strip(), "tema": tema.strip() if tema else None})


if __name__ == "__main__":
    clara_mcp.run(transport="stdio")
