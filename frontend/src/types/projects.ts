// Project Discovery Types

export interface SREDSignals {
  uncertainty: number
  systematic: number
  failure: number
  advancement: number
}

export interface ProjectCandidate {
  name: string
  document_count: number
  document_ids: string[]
  start_date: string | null
  end_date: string | null
  team_members: string[]
  sred_score: number
  confidence: number
  signals: SREDSignals
  summary: string
}

export interface DiscoverProjectsRequest {
  claim_id: string
  backfill_signals?: boolean
  min_cluster_size?: number
}

export interface DiscoverProjectsResponse {
  success: boolean
  run_id: string
  total_documents: number
  high_confidence: ProjectCandidate[]
  medium_confidence: ProjectCandidate[]
  low_confidence: ProjectCandidate[]
  message: string | null
}

export interface SaveProjectsRequest {
  claim_id: string
  candidates: ProjectCandidate[]
}

export interface SaveProjectsResponse {
  success: boolean
  projects_created: number
  project_ids: string[]
  message: string
}

export interface ProjectSummary {
  id: string
  project_name: string
  project_code: string | null
  project_status: 'discovered' | 'approved' | 'rejected' | 'archived'
  sred_confidence_score: number | null
  document_count: number
  project_start_date: string | null
  project_end_date: string | null
  discovery_method: string | null
  ai_suggested: boolean
  user_confirmed: boolean
  created_at: string
}

export interface ProjectListResponse {
  success: boolean
  projects: ProjectSummary[]
  total: number
}

export interface ProjectDetail extends ProjectSummary {
  claim_id: string
  company_id: string
  team_members: string[]
  team_size: number
  estimated_spend: number | null
  eligible_expenditures: number | null
  uncertainty_signal_count: number
  systematic_signal_count: number
  failure_signal_count: number
  advancement_signal_count: number
  ai_summary: string | null
  uncertainty_summary: string | null
  work_summary: string | null
  advancement_summary: string | null
  narrative_status: 'not_started' | 'draft' | 'review' | 'approved'
  narrative_line_242: string | null
  narrative_line_244: string | null
  narrative_line_246: string | null
  narrative_word_count_242: number | null
  narrative_word_count_244: number | null
  narrative_word_count_246: number | null
  updated_at: string | null
}

export interface ProjectDetailResponse {
  success: boolean
  project: ProjectDetail
}

export interface UpdateProjectRequest {
  project_name?: string
  project_code?: string
  project_status?: string
  team_members?: string[]
  estimated_spend?: number
  narrative_line_242?: string
  narrative_line_244?: string
  narrative_line_246?: string
}

export interface ProjectDocument {
  id: string
  document_id: string
  document_title: string
  original_filename: string
  document_type: string | null
  document_date: string | null
  tagged_by: 'ai' | 'user'
  confidence_score: number | null
  sred_signals: SREDSignals | null
  ai_summary: string | null
  created_at: string
}

export interface ProjectDocumentsResponse {
  success: boolean
  documents: ProjectDocument[]
  total: number
}

export interface AddDocumentsRequest {
  document_ids: string[]
}

// Change Detection Types

export interface AnalyzeBatchRequest {
  claim_id: string
  document_ids?: string[]
  batch_id?: string
}

export interface ProjectAddition {
  project_id: string
  project_name: string
  document_ids: string[]
  document_count: number
  confidence: 'high' | 'medium' | 'low'
  average_similarity: number
  summary: string
}

export interface NewProjectCandidate {
  name: string
  document_ids: string[]
  document_count: number
  confidence: number
  sred_score: number
  summary: string
}

export interface NarrativeImpact {
  project_id: string
  project_name: string
  severity: 'high' | 'medium' | 'low'
  impact_type: 'contradiction' | 'enhancement' | 'gap' | 'new_evidence'
  description: string
  document_ids: string[]
  affected_line: number | null
}

export interface ChangeAnalysisResponse {
  success: boolean
  batch_id: string | null
  total_new_documents: number
  additions_to_existing: ProjectAddition[]
  new_projects_discovered: NewProjectCandidate[]
  narrative_impacts: NarrativeImpact[]
  unassigned_count: number
  unassigned_document_ids: string[]
}

export interface ApplyAdditionsRequest {
  additions: ProjectAddition[]
}

export interface ApplyAdditionsResponse {
  success: boolean
  tags_created: number
  message: string
}

export interface GenericResponse {
  success: boolean
  message: string | null
  data?: Record<string, unknown>
}
