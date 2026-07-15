"""Local, session-scoped curriculum coverage. No pack snapshots are retained."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.curriculum.provider import JsonCurriculumProvider
from app.models.coverage import CoverageObjective, CoverageOverview
from app.models.teaching_pack import ActivityGuide, LessonPlan, ReviewFinding, ReviewReport


SCHEMA = """
CREATE TABLE IF NOT EXISTS teacher_sessions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS packs (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES teacher_sessions(id),
  source_type TEXT NOT NULL CHECK(source_type IN ('generated', 'imported_audit')),
  subject TEXT NOT NULL,
  grade_level TEXT NOT NULL,
  created_at TEXT NOT NULL,
  review_status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pack_objectives (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pack_id TEXT NOT NULL REFERENCES packs(id),
  objective_code TEXT NOT NULL,
  declared_text TEXT NOT NULL,
  verification_state TEXT NOT NULL CHECK(verification_state IN ('verified', 'invalid', 'unverified')),
  verified_description TEXT,
  worked_in_activities INTEGER NOT NULL CHECK(worked_in_activities IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_packs_session_subject_level ON packs(session_id, subject, grade_level);
CREATE INDEX IF NOT EXISTS idx_pack_objectives_pack_code ON pack_objectives(pack_id, objective_code);
"""


def _database(path: str | Path) -> sqlite3.Connection:
    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def _verified_by_code(trace: list[dict]) -> dict[str, dict]:
    return {
        str(call["arguments"]["codigo"]).casefold(): call["result"]
        for call in trace
        if call.get("tool") == "verificar_objetivo" and isinstance(call.get("arguments"), dict) and isinstance(call.get("result"), dict)
    }


def _worked_in_activities(code: str, guide: ActivityGuide, review: ReviewReport) -> bool:
    """Only count activity evidence when the per-pack reviewer did not flag this OA as unworked."""
    if not guide.activities or not guide.targeted_learning_objectives:
        return False
    code_folded = code.casefold()
    return not any(
        finding.category == "objective_coherence"
        and (finding.artifact_id.casefold() == code_folded or code_folded in finding.description.casefold())
        for finding in review.findings
    )


def record_reviewed_pack(*, database_path: str | Path, session_id: str | None, source_type: str, plan: LessonPlan, activities: ActivityGuide, review: ReviewReport, verification_trace: list[dict]) -> str | None:
    """Persist claims and evidence, never a full lesson/assessment snapshot."""
    if not session_id:
        return None
    now = datetime.now(timezone.utc).isoformat()
    pack_id = str(uuid4())
    verified = _verified_by_code(verification_trace)
    connection = _database(database_path)
    try:
        with connection:
            connection.execute("INSERT OR IGNORE INTO teacher_sessions(id, created_at, last_seen_at) VALUES (?, ?, ?)", (session_id, now, now))
            connection.execute("UPDATE teacher_sessions SET last_seen_at = ? WHERE id = ?", (now, session_id))
            connection.execute("INSERT INTO packs(id, session_id, source_type, subject, grade_level, created_at, review_status) VALUES (?, ?, ?, ?, ?, ?, ?)", (pack_id, session_id, source_type, plan.subject, plan.grade_level, now, review.status))
            for objective in plan.curriculum_alignment.objectives:
                result = verified.get(objective.code.casefold())
                state = "verified" if result and result.get("existe") else "invalid" if result else "unverified"
                official = result.get("objetivo") if result else None
                connection.execute(
                    "INSERT INTO pack_objectives(pack_id, objective_code, declared_text, verification_state, verified_description, worked_in_activities) VALUES (?, ?, ?, ?, ?, ?)",
                    (pack_id, objective.code, objective.description, state, official.get("description") if official else None, int(_worked_in_activities(objective.code, activities, review))),
                )
    finally:
        connection.close()
    return pack_id


def coverage_overview(*, database_path: str | Path, session_id: str, subject: str, grade_level: str, provider: JsonCurriculumProvider | None = None) -> CoverageOverview:
    provider = provider or JsonCurriculumProvider()
    universe = provider.candidates(subject, grade_level)
    official = {entry.objective.code: entry.objective for entry in universe}
    connection = _database(database_path)
    try:
        with connection:
            rows = connection.execute(
                """SELECT po.*, p.created_at FROM pack_objectives po JOIN packs p ON p.id = po.pack_id
                   WHERE p.session_id = ? AND p.subject = ? AND p.grade_level = ?""",
                (session_id, subject, grade_level),
            ).fetchall()
            pack_count = connection.execute("SELECT COUNT(*) FROM packs WHERE session_id = ? AND subject = ? AND grade_level = ?", (session_id, subject, grade_level)).fetchone()[0]
    finally:
        connection.close()
    by_code: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_code.setdefault(row["objective_code"], []).append(row)
    objectives: list[CoverageObjective] = []
    for code, objective in official.items():
        objective_rows = by_code.get(code, [])
        worked = [row for row in objective_rows if row["verification_state"] == "verified" and row["worked_in_activities"]]
        unverified = [row for row in objective_rows if row["verification_state"] != "verified"]
        no_evidence = [row for row in objective_rows if row["verification_state"] == "verified" and not row["worked_in_activities"]]
        objectives.append(CoverageObjective(
            code=code, description=objective.description, coverage_count=len(worked), declared_unverified_count=len(unverified), declared_without_activity_evidence_count=len(no_evidence), pack_dates=[datetime.fromisoformat(row["created_at"]) for row in worked], status="trabajado" if worked else "aun_no_visto",
        ))
    findings = _longitudinal_findings(subject, grade_level, pack_count, objectives)
    scope_note = "Esta cobertura refleja únicamente los packs generados o auditados por Clara en esta sesión. No describe todas tus clases ni tu cobertura anual completa."
    if not universe:
        scope_note += " Clara no tiene OA disponibles para esta asignatura y nivel, por lo que no puede afirmar qué objetivos nunca se han trabajado."
    return CoverageOverview(
        subject=subject, grade_level=grade_level, reviewed_pack_count=pack_count,
        scope_note=scope_note,
        objectives=objectives, longitudinal_findings=findings,
    )


def _longitudinal_findings(subject: str, grade_level: str, pack_count: int, objectives: list[CoverageObjective]) -> list[ReviewFinding]:
    if not pack_count:
        return []
    untouched = [objective for objective in objectives if objective.coverage_count == 0]
    findings: list[ReviewFinding] = [
        ReviewFinding(id=f"coverage-gap-{objective.code}", severity="importante", responsible_agent="planner", category="coverage", artifact_type="plan", artifact_id=objective.code,
                      description=f"De los {pack_count} packs revisados por Clara para {subject} {grade_level}, no encontré ninguno que trabaje {objective.code}.", suggested_correction="Considera incorporar este OA en una próxima clase si corresponde a tu planificación anual.")
        for objective in untouched
    ]
    for objective in objectives:
        if objective.coverage_count >= 3 and untouched:
            findings.append(ReviewFinding(id=f"coverage-repeated-{objective.code}", severity="menor", responsible_agent="planner", category="coverage", artifact_type="plan", artifact_id=objective.code,
                                          description=f"{objective.code} aparece trabajado en {objective.coverage_count} packs revisados, mientras {', '.join(item.code for item in untouched)} aún no aparece trabajado en los materiales que Clara ha visto.", suggested_correction="Revisa si la repetición responde a una decisión pedagógica o si conviene equilibrar próximos objetivos."))
        if objective.declared_without_activity_evidence_count:
            findings.append(ReviewFinding(id=f"coverage-declared-{objective.code}", severity="importante", responsible_agent="planner", category="coverage", artifact_type="plan", artifact_id=objective.code,
                                          description=f"{objective.code} fue declarado y verificado en {objective.declared_without_activity_evidence_count} pack(s), pero Clara no encontró evidencia suficiente de actividades que lo trabajaran.", suggested_correction="Revisa las actividades de esos packs antes de contarlos como cobertura curricular."))
    return findings
