export interface LessonRequest {
  description: string;
  subject: string;
  grade_level: string;
  topic: string;
  duration_minutes: number;
  notes?: string;
}

export interface CurriculumObjective { code: string; description: string; source: string }
export interface CurriculumAlignment { status: "aligned" | "partial" | "not_found"; notes: string[]; objectives: CurriculumObjective[] }
export interface LessonStage { name: string; duration_minutes: number; purpose: string; formative_check?: string }
export interface LessonPlan {
  title: string; subject: string; grade_level: string; duration_minutes: number;
  curriculum_alignment: CurriculumAlignment; learning_objectives: string[];
  key_concepts: string[]; prerequisite_knowledge: string[]; materials: string[]; stages: LessonStage[];
}
export interface ActivityDifferentiation { support: string; extension: string }
export interface ClassroomActivity {
  id: string;
  stage_name: string; title: string; duration_minutes: number;
  grouping: "individual" | "parejas" | "grupos" | "curso completo";
  purpose: string; teacher_instructions: string[]; expected_student_output: string;
  materials: string[]; differentiation: ActivityDifferentiation;
}
export interface ActivityGuide {
  title: string; overview: string; targeted_learning_objectives: string[];
  activities: ClassroomActivity[]; materials_summary: string[];
}
export interface AssessmentOption { label: string; text: string }
export interface AssessmentItem { id: string; type: "selección múltiple" | "respuesta breve" | "desarrollo"; question: string; options: AssessmentOption[]; correct_option_label?: string; expected_answer: string; points: number; learning_objective: string; cognitive_level: "recordar" | "comprender" | "aplicar" | "analizar" }
export interface RubricCriterion { criterion: string; item_ids: string[]; levels: { logrado: string; en_proceso: string; requiere_apoyo: string } }
export interface SpecificationRow { learning_objective: string; item_count: number; item_ids: string[]; total_points: number; cognitive_levels: string[] }
export interface Assessment { title: string; instructions: string[]; suggested_application_minutes: number; total_points: number; specification_table: SpecificationRow[]; items: AssessmentItem[]; rubric: RubricCriterion[] }
export interface PrintableBlock { type: "texto" | "tabla" | "tarjetas" | "organizador" | "preguntas"; title?: string; content?: string; columns: string[]; rows: string[][]; cards: Record<string, string>[]; fields: Record<string, string>[]; questions: Record<string, string | number>[] }
export interface PrintableMaterial { id: string; activity_id: string; source_material_label: string; type: string; title: string; student_instructions: string[]; content: PrintableBlock[] }
export interface MaterialCoverage { activity_id: string; source_material_label: string; fulfillment: "material_generado" | "evaluacion_estudiante" | "sin_cobertura"; material_id?: string }
export interface MaterialPack { title: string; materials: PrintableMaterial[]; coverage: MaterialCoverage[] }
export interface ReviewFinding { id: string; severity: "bloqueante" | "importante" | "menor"; responsible_agent: "planner" | "designer" | "assessment" | "materials"; category: string; artifact_type: string; artifact_id: string; description: string; suggested_correction: string }
export interface ReviewReport { status: "clean" | "findings_remaining"; summary: string; findings: ReviewFinding[]; correction: { attempted: boolean; target_agent?: string; outcome?: string } }
export interface ParseNote { severity: "importante" | "menor"; artifact_type: string; artifact_id?: string; field?: string; message: string; source_excerpt?: string }
export interface AuditReport { overall_status: "listo_para_revisar" | "requiere_atencion"; source_summary: string; parse_confidence: "alta" | "media" | "baja"; parse_notes: ParseNote[]; findings: ReviewFinding[] }
export type GenerationEvent =
  | { type: "agent_tool_completed"; agent: "planner" | "reviewer"; tool: string; summary: string }
  | { type: "planner_started"; message: string }
  | { type: "planner_completed"; plan: LessonPlan }
  | { type: "designer_started"; message: string }
  | { type: "designer_completed"; activities: ActivityGuide }
  | { type: "assessment_started"; message: string }
  | { type: "assessment_completed"; assessment: Assessment }
  | { type: "reviewer_started"; message: string }
  | { type: "reviewer_correcting"; target_agent: string; message: string }
  | { type: "reviewer_completed"; review: ReviewReport; activities: ActivityGuide; assessment: Assessment }
  | { type: "materials_started"; message: string }
  | { type: "materials_completed"; materials: MaterialPack }
  | { type: "materials_reviewer_started"; message: string }
  | { type: "materials_reviewer_correcting"; message: string }
  | { type: "materials_reviewer_completed"; materials: MaterialPack; review: ReviewReport }
  | { type: "materials_failure"; message: string }
  | { type: "audit_parse_started"; message: string }
  | { type: "audit_parse_completed"; bundle: unknown }
  | { type: "audit_reviewer_started"; message: string }
  | { type: "audit_completed"; report: AuditReport }
  | { type: "audit_failure"; message: string }
  | { type: "edited_review_started"; message: string }
  | { type: "edited_review_completed"; review: ReviewReport }
  | { type: "edited_review_failure"; message: string }
  | { type: "failure"; message: string };
