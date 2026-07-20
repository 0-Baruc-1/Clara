export type ClaraRole = "teacher" | "student";

export interface PublishedMaterialRelease {
  release_id: string;
  title: string;
  released_at: string;
}

export interface StudentPracticeItem {
  id: string;
  ordinal: number;
  item_snapshot: Record<string, unknown>;
  evidence_objective_code: string | null;
  validation_mode: "deterministic" | "teacher_judgment";
}

export interface StudentPracticeMaterial {
  release_id: string;
  publication_version_id: string;
  title: string;
  items: StudentPracticeItem[];
}

export interface StudentResponseReceipt {
  response_attempt_id: string;
  feedback_state: "verified" | "not_applicable" | "unavailable";
  feedback_message: string;
}

export interface PublishPracticeMaterialResponse {
  publication_version_id: string;
  release_id: string;
  published_item_count: number;
  attested_objective_codes: string[];
  practice_only_item_count: number;
  note: string;
}

export interface StudentObjectiveEvidence {
  student_id: string;
  student_full_name: string | null;
  objective_code: string;
  declared_publication_count: number;
  attested_item_count: number;
  distinct_items_responded: number;
  evidence_threshold: number;
  state: "evidencia_suficiente" | "evidencia_insuficiente";
  wording: string;
}

export interface PracticeItemForPublication {
  source_assessment_item_id?: string | null;
  ordinal: number;
  item_snapshot: Record<string, unknown>;
  requested_evidence_objective_code?: string | null;
  deterministic_validator_candidate?: null;
}

export interface PublishPracticeMaterialRequest {
  class_id: string;
  source_pack_reference: string;
  source_pack_version_reference?: string | null;
  source_review_reference?: string | null;
  title: string;
  content_snapshot: Record<string, unknown>;
  declared_objective_codes: string[];
  attestation_statement_version: string;
  items: PracticeItemForPublication[];
}
