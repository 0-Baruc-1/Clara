"""Provider-backed Responses API tools. No curriculum data lives here."""
from collections.abc import Callable
from typing import Any
from app.curriculum.provider import CurriculumProvider, normalized

CURRICULUM_TOOLS = [
 {"type":"function","name":"buscar_objetivos","description":"Busca Objetivos de Aprendizaje oficiales por asignatura, nivel y tema.","parameters":{"type":"object","properties":{"asignatura":{"type":"string"},"nivel":{"type":"string"},"tema":{"type":["string","null"]}},"required":["asignatura","nivel","tema"],"additionalProperties":False},"strict":True},
 {"type":"function","name":"verificar_objetivo","description":"Verifica un código OA contra la fuente curricular oficial.","parameters":{"type":"object","properties":{"codigo":{"type":"string"}},"required":["codigo"],"additionalProperties":False},"strict":True},
 {"type":"function","name":"listar_asignaturas_niveles","description":"Lista la cobertura disponible de asignaturas y niveles.","parameters":{"type":"object","properties":{},"required":[],"additionalProperties":False},"strict":True},
]
class CurriculumToolFailure(RuntimeError): pass
def _tokens(value: str) -> set[str]: return {token for token in normalized(value).split() if len(token) > 2}
def curriculum_tool_handler(provider: CurriculumProvider, trace: list[dict[str, Any]]) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
    verified: dict[str, dict[str, Any]] = {}
    def execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
        try:
            if name == "buscar_objetivos":
                candidates = provider.candidates(args["asignatura"], args["nivel"])
                topic = _tokens(args.get("tema") or "")
                if topic:
                    relevant = [entry for entry in candidates if topic & _tokens(entry.objective.description + " " + " ".join(entry.keywords))]
                    if relevant: candidates = relevant  # Never turn valid coverage into false empty.
                result = {"cobertura_encontrada": bool(candidates), "objetivos": [entry.model_dump(mode="json") for entry in candidates]}
            elif name == "verificar_objetivo":
                code = args["codigo"].casefold(); entry = provider.find_by_code(args["codigo"])
                result = verified.setdefault(code, {"existe": bool(entry), "objetivo": entry.model_dump(mode="json") if entry else None, "mensaje": "OA verificado." if entry else "El código OA no existe en la fuente curricular."})
            elif name == "listar_asignaturas_niveles": result = {"cobertura": provider.coverage()}
            else: raise CurriculumToolFailure(f"Herramienta curricular desconocida: {name}")
        except Exception as error: raise CurriculumToolFailure("La fuente curricular no está disponible; no es seguro continuar sin verificar OA.") from error
        trace.append({"tool": name, "arguments": args, "result": result}); return result
    return execute
