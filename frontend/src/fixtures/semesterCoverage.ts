import type { CoverageOverview } from "../types/teachingPack";

export const mockCoverageOverview: CoverageOverview = {
  subject: "Ciencias Naturales", grade_level: "6° básico", reviewed_pack_count: 5,
  scope_note: "Esta cobertura refleja únicamente los packs generados o auditados por Clara en esta sesión. No describe todas tus clases ni tu cobertura anual completa.",
  objectives: [
    { code: "CN06 OA 13", description: "Demostrar, mediante investigación experimental, los cambios de estado de la materia.", coverage_count: 3, declared_unverified_count: 0, declared_without_activity_evidence_count: 0, pack_dates: ["2026-03-12T12:00:00Z", "2026-03-19T12:00:00Z", "2026-04-02T12:00:00Z"], status: "trabajado" },
    { code: "CN06 OA 14", description: "Diferenciar entre calor y temperatura.", coverage_count: 0, declared_unverified_count: 0, declared_without_activity_evidence_count: 0, pack_dates: [], status: "aun_no_visto" },
    { code: "CN06 OA 15", description: "Medir e interpretar información al calentar y enfriar el agua.", coverage_count: 1, declared_unverified_count: 1, declared_without_activity_evidence_count: 1, pack_dates: ["2026-04-16T12:00:00Z"], status: "trabajado" },
  ],
  longitudinal_findings: [
    { id: "coverage-gap-CN06-OA-14", severity: "importante", responsible_agent: "planner", category: "coverage", artifact_type: "plan", artifact_id: "CN06 OA 14", description: "De los 5 packs revisados por Clara para Ciencias Naturales 6° básico, no encontré ninguno que trabaje CN06 OA 14.", suggested_correction: "Considera incorporarlo en una próxima clase si corresponde a tu planificación anual." },
    { id: "coverage-repeat-CN06-OA-13", severity: "menor", responsible_agent: "planner", category: "coverage", artifact_type: "plan", artifact_id: "CN06 OA 13", description: "CN06 OA 13 aparece trabajado en 3 packs revisados, mientras CN06 OA 14 aún no aparece trabajado en los materiales que Clara ha visto.", suggested_correction: "Revisa si la repetición responde a una decisión pedagógica o si conviene equilibrar próximos objetivos." },
  ],
};
