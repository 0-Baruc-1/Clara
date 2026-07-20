"""Narrow Supabase REST/RPC adapter for the student evidence schema."""
from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from app.core.config import settings
from app.models.student_section import (
    PreparedPublication,
    StudentObjectiveEvidence,
    StudentMaterialRelease,
    StudentPracticeItem,
    StudentPracticeMaterial,
)


class StudentStoreUnavailable(RuntimeError):
    pass


class SupabaseStudentStore:
    def _require_config(self) -> None:
        if not settings.supabase_url or not settings.supabase_anon_key or not settings.supabase_service_role_key:
            raise StudentStoreUnavailable("La conexión segura de estudiantes no está configurada.")

    @property
    def _rest_url(self) -> str:
        assert settings.supabase_url
        return f"{settings.supabase_url.rstrip('/')}/rest/v1"

    async def _rpc(self, name: str, payload: dict[str, Any], *, access_token: str | None = None, service_role: bool = False) -> Any:
        self._require_config()
        assert settings.supabase_anon_key and settings.supabase_service_role_key
        bearer = settings.supabase_service_role_key if service_role else access_token
        if not bearer:
            raise StudentStoreUnavailable("Falta una sesión autenticada para esta operación.")
        headers = {"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {bearer}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(f"{self._rest_url}/rpc/{name}", headers=headers, json=payload)
            if response.is_error:
                raise StudentStoreUnavailable("Supabase rechazó la operación de estudiantes.")
            return response.json()
        except httpx.HTTPError as error:
            raise StudentStoreUnavailable("No fue posible comunicarse con la sección de estudiantes.") from error

    async def publish(self, *, teacher_id: UUID, access_token: str, prepared: PreparedPublication, class_id: UUID) -> tuple[UUID, UUID]:
        payload = {
            "class_id": str(class_id),
            **prepared.model_dump(mode="json", exclude={"objectives"}),
        }
        ticket_id = await self._rpc(
            "clara_create_publication_verification_ticket",
            {
                "p_teacher_id": str(teacher_id),
                "p_payload": payload,
                "p_verified_objectives": [objective.model_dump(mode="json") for objective in prepared.objectives],
            },
            service_role=True,
        )
        version_id = await self._rpc(
            "clara_publish_student_material",
            {"p_payload": payload, "p_ticket_id": ticket_id},
            access_token=access_token,
        )
        publication_version_id = UUID(str(version_id))
        # The database trigger creates the release in the same transaction as
        # the status transition. Read the stored relation back rather than
        # reconstructing it client-side.
        rows = await self._rest_get(
            "student_material_releases",
            {"publication_version_id": f"eq.{publication_version_id}", "select": "id"},
            access_token=access_token,
        )
        if not isinstance(rows, list) or len(rows) != 1 or not rows[0].get("id"):
            raise StudentStoreUnavailable("La publicación se creó, pero no fue posible recuperar su acceso para estudiantes.")
        return publication_version_id, UUID(str(rows[0]["id"]))

    async def _rest_get(self, table: str, query: dict[str, str], *, access_token: str) -> Any:
        """Read a RLS-protected relation using the authenticated user's token."""
        self._require_config()
        assert settings.supabase_anon_key
        headers = {"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {access_token}"}
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(f"{self._rest_url}/{table}", headers=headers, params=query)
            if response.is_error:
                raise StudentStoreUnavailable("Supabase rechazó la consulta de material publicado.")
            return response.json()
        except httpx.HTTPError as error:
            raise StudentStoreUnavailable("No fue posible comunicarse con la sección de estudiantes.") from error

    async def student_material(self, *, release_id: UUID, access_token: str) -> StudentPracticeMaterial:
        rows = await self._rpc("clara_student_material_snapshot", {"p_release_id": str(release_id)}, access_token=access_token)
        if not isinstance(rows, list) or not rows:
            raise StudentStoreUnavailable("Este material ya no está disponible.")
        first = rows[0]
        return StudentPracticeMaterial(
            release_id=UUID(str(first["release_id"])),
            publication_version_id=UUID(str(first["publication_version_id"])),
            title=str(first["title"]),
            items=[
                StudentPracticeItem(
                    id=UUID(str(row["item_id"])), ordinal=int(row["ordinal"]),
                    item_snapshot=row["item_snapshot"], evidence_objective_code=row.get("evidence_objective_code"),
                    validation_mode=row["validation_mode"],
                )
                for row in rows
            ],
        )

    async def student_material_releases(self, *, access_token: str) -> list[StudentMaterialRelease]:
        """List only active releases the current student can read under RLS."""
        rows = await self._rest_get(
            "student_material_releases",
            {
                "is_active": "eq.true",
                "select": "id,title_snapshot,released_at",
                "order": "released_at.desc",
            },
            access_token=access_token,
        )
        if not isinstance(rows, list):
            raise StudentStoreUnavailable("No fue posible leer los materiales disponibles.")
        return [
            StudentMaterialRelease(
                release_id=UUID(str(row["id"])),
                title=str(row["title_snapshot"]),
                released_at=str(row["released_at"]),
            )
            for row in rows
        ]

    async def own_role(self, *, user_id: UUID, access_token: str) -> str | None:
        """Read only the caller's role through the same RLS policy as the UI."""
        rows = await self._rest_get(
            "clara_user_roles",
            {"user_id": f"eq.{user_id}", "select": "role"},
            access_token=access_token,
        )
        if not isinstance(rows, list) or len(rows) != 1:
            return None
        value = rows[0].get("role")
        return str(value) if value is not None else None

    async def submit_response(self, *, item_id: UUID, answer: str, access_token: str) -> UUID:
        value = await self._rpc(
            "clara_submit_student_response",
            {"p_published_item_id": str(item_id), "p_answer_payload": {"answer": answer}},
            access_token=access_token,
        )
        return UUID(str(value))

    async def item_validation(self, item_id: UUID) -> tuple[str, dict[str, Any] | None]:
        rows = await self._rpc(
            "clara_host_item_validation", {"p_item_id": str(item_id)}, service_role=True
        )
        if not isinstance(rows, list) or not rows:
            raise StudentStoreUnavailable("No fue posible consultar el validador publicado.")
        return str(rows[0].get("validation_mode")), rows[0].get("deterministic_validator")

    async def attach_feedback(self, *, response_attempt_id: UUID, feedback: dict[str, Any]) -> None:
        await self._rpc(
            "clara_attach_host_feedback",
            {"p_response_attempt_id": str(response_attempt_id), "p_feedback": feedback},
            service_role=True,
        )

    async def teacher_evidence(self, *, class_id: UUID, access_token: str) -> list[StudentObjectiveEvidence]:
        rows = await self._rpc(
            "clara_teacher_student_evidence", {"p_class_id": str(class_id)}, access_token=access_token
        )
        if not isinstance(rows, list):
            raise StudentStoreUnavailable("No fue posible leer la evidencia del curso.")
        result: list[StudentObjectiveEvidence] = []
        for row in rows:
            responded = int(row["distinct_items_responded"])
            total = int(row["attested_item_count"])
            threshold = int(row["evidence_threshold"])
            result.append(StudentObjectiveEvidence(
                student_id=UUID(str(row["student_id"])),
                student_full_name=str(row["student_full_name"]) if row.get("student_full_name") else None,
                objective_code=str(row["objective_code"]),
                declared_publication_count=int(row["declared_publication_count"]),
                attested_item_count=total,
                distinct_items_responded=responded,
                evidence_threshold=threshold,
                state=row["evidence_state"],
                wording=(
                    f"Respondió {responded} de {total} ítems que etiquetaste {row['objective_code']}."
                    if responded >= threshold else
                    f"Evidencia insuficiente: respondió {responded} de {total} ítems que etiquetaste {row['objective_code']}; el umbral del curso es {threshold}."
                ),
            ))
        return result
