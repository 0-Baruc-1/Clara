"""Host-side preparation and deterministic feedback for student practice.

An LLM may suggest a validator, but this module is the only place where a
candidate becomes a frozen deterministic recipe.  Everything else is teacher
judgment by default.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sympy import Add, Float, Integer, Mul, Pow, Rational, Symbol, simplify, preorder_traversal
from sympy.parsing.sympy_parser import parse_expr

from app.curriculum.provider import CurriculumProvider
from app.models.student_section import (
    DeterministicValidatorCandidate,
    PreparedPracticeItem,
    PreparedPublication,
    PublicationObjectiveAttestation,
    PublishPracticeMaterialRequest,
)


class DeterministicValidationError(ValueError):
    """A recipe is unsuitable for safe, host-verifiable feedback."""


_EXPRESSION_PATTERN = re.compile(r"^[0-9xX+\-*/^().,\s]+$")
_ALLOWED_NODE_TYPES = (Integer, Rational, Float, Add, Mul, Pow, Symbol)
_PARSE_GLOBALS = {
    "__builtins__": {},
    "Integer": Integer,
    "Rational": Rational,
    "Float": Float,
    "Symbol": Symbol,
    "Add": Add,
    "Mul": Mul,
    "Pow": Pow,
}
_PARSE_LOCALS = {"x": Symbol("x")}
_MAX_EXPRESSION_LENGTH = 128
_MAX_EXPRESSION_NODES = 64


def _safe_parse_expression(raw: str, allowed_symbols: set[str]) -> Any:
    """Parse a tiny arithmetic grammar without raw ``eval`` or ``sympify``.

    ``parse_expr(..., evaluate=False)`` is constrained twice: lexical input is
    limited to arithmetic characters, then every parsed node and symbol is
    allow-listed. This is intentionally narrow; unsupported math falls back to
    teacher judgment instead of expanding the execution surface.
    """
    value = raw.strip().replace("^", "**").replace(",", ".")
    if not value or len(value) > _MAX_EXPRESSION_LENGTH or not _EXPRESSION_PATTERN.fullmatch(raw):
        raise DeterministicValidationError("La expresión no pertenece al subconjunto aritmético permitido.")
    try:
        expression = parse_expr(
            value,
            local_dict=_PARSE_LOCALS,
            global_dict=_PARSE_GLOBALS,
            evaluate=False,
        )
    except Exception as error:
        raise DeterministicValidationError("No fue posible interpretar la expresión aritmética.") from error
    nodes = list(preorder_traversal(expression))
    if len(nodes) > _MAX_EXPRESSION_NODES or any(not isinstance(node, _ALLOWED_NODE_TYPES) for node in nodes):
        raise DeterministicValidationError("La expresión usa operaciones no permitidas.")
    names = {str(symbol) for symbol in expression.free_symbols}
    if names - allowed_symbols:
        raise DeterministicValidationError("La expresión usa símbolos no permitidos.")
    for node in nodes:
        if isinstance(node, Pow):
            exponent = node.exp
            if not isinstance(exponent, Rational) or abs(exponent) > 6:
                raise DeterministicValidationError(
                    "Las potencias solo admiten exponentes racionales literales con magnitud menor o igual a 6."
                )
    return expression


def freeze_deterministic_validator(candidate: DeterministicValidatorCandidate | None) -> dict[str, Any] | None:
    """Validate a candidate once at publication; return the immutable recipe."""
    if candidate is None or candidate.kind != "sympy_equivalence":
        return None
    allowed_symbols = set(candidate.allowed_symbols)
    expression = _safe_parse_expression(candidate.expected_expression, allowed_symbols)
    # Store only the constrained source text, never arbitrary model payload.
    return {
        "kind": "sympy_equivalence",
        "expected_expression": str(expression),
        "allowed_symbols": sorted(allowed_symbols),
        "validator_version": 1,
    }


def deterministic_feedback(recipe: dict[str, Any], student_answer: str) -> dict[str, Any]:
    """Evaluate only a frozen, previously host-validated recipe."""
    if recipe.get("kind") != "sympy_equivalence" or recipe.get("validator_version") != 1:
        raise DeterministicValidationError("La receta congelada no es válida.")
    allowed_symbols = set(recipe.get("allowed_symbols", []))
    expected = _safe_parse_expression(str(recipe.get("expected_expression", "")), allowed_symbols)
    received = _safe_parse_expression(student_answer, allowed_symbols)
    try:
        matches = bool(simplify(received - expected) == 0)
    except Exception as error:
        raise DeterministicValidationError("No fue posible comprobar la respuesta de forma determinista.") from error
    return {
        "matches_expected_answer": matches,
        "message": "Tu resultado coincide con la respuesta esperada." if matches else "Tu resultado no coincide todavía. Revisa el procedimiento e inténtalo nuevamente.",
    }


@dataclass(frozen=True)
class PreparedPublicationResult:
    publication: PreparedPublication
    excluded_objective_codes: list[str]


def prepare_publication_for_attestation(
    request: PublishPracticeMaterialRequest,
    provider: CurriculumProvider,
) -> PreparedPublicationResult:
    """Resolve OA labels against the provider without dropping practice items.

    A missing/unavailable OA removes only the evidence claim. The teacher can
    still publish the item as practice, explicitly marked as having no OA
    evidence. Provider failures therefore cannot become unverified labels.
    """
    verification_run_id = f"publication-{uuid4()}"
    requested_codes = {item.requested_evidence_objective_code for item in request.items if item.requested_evidence_objective_code}
    verified: dict[str, PublicationObjectiveAttestation] = {}
    unavailable_codes: set[str] = set()
    for code in requested_codes:
        try:
            entry = provider.find_by_code(code)
        except Exception:
            entry = None
        if entry is None:
            unavailable_codes.add(code)
            continue
        verified[code.casefold()] = PublicationObjectiveAttestation(
            objective_code=entry.objective.code,
            official_wording_snapshot=entry.objective.description,
            curriculum_source_url=entry.objective.source,
            verification_run_id=verification_run_id,
        )

    items: list[PreparedPracticeItem] = []
    for item in request.items:
        requested_code = item.requested_evidence_objective_code
        attested = verified.get(requested_code.casefold()) if requested_code else None
        try:
            frozen_validator = freeze_deterministic_validator(item.deterministic_validator_candidate)
        except DeterministicValidationError:
            frozen_validator = None
        items.append(
            PreparedPracticeItem(
                source_assessment_item_id=item.source_assessment_item_id,
                ordinal=item.ordinal,
                item_snapshot=item.item_snapshot,
                evidence_objective_code=attested.objective_code if attested else None,
                evidence_exclusion_reason=None if attested else ("oa_no_verificable" if requested_code else "sin_etiqueta_oa"),
                validation_mode="deterministic" if frozen_validator else "teacher_judgment",
                deterministic_validator=frozen_validator,
            )
        )
    publication = PreparedPublication(
        source_pack_reference=request.source_pack_reference,
        source_pack_version_reference=request.source_pack_version_reference,
        source_review_reference=request.source_review_reference,
        title=request.title,
        content_snapshot=request.content_snapshot,
        declared_objective_codes=list(dict.fromkeys(request.declared_objective_codes)),
        attestation_statement_version=request.attestation_statement_version,
        objectives=list(verified.values()),
        items=items,
    )
    return PreparedPublicationResult(
        publication=publication,
        excluded_objective_codes=sorted(unavailable_codes),
    )
