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
export type GenerationEvent =
  | { type: "planner_started"; message: string }
  | { type: "planner_completed"; plan: LessonPlan }
  | { type: "designer_started"; message: string }
  | { type: "designer_completed"; activities: ActivityGuide }
  | { type: "assessment_started"; message: string }
  | { type: "assessment_completed"; assessment: Assessment }
  | { type: "failure"; message: string };
